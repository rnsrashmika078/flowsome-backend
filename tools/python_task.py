import operator
import re
import subprocess
import sys
from typing import Annotated

from langchain.tools import ToolRuntime
from langchain_ollama import ChatOllama
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from agent.models import CHAT_MODEL, CODING_MODEL

MAX_RESULT_CHARS = 2000
MAX_SCRIPTS_IN_PROMPT = 2
SCRIPT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_ATTEMPTS = 5

llm = ChatOllama(model=CODING_MODEL, reasoning=False, temperature=0.4)


class PythonTaskState(TypedDict):
    task: str
    python_script: str
    result: str
    status: str
    previous_script: Annotated[list[str], operator.add]
    attempt: int
    max_attempt: int
    output_file_path: str


class GeneratedScript(BaseModel):
    script: str = Field(..., description="Python script for the requested task")


def _script_prompt(state: PythonTaskState) -> str:
    return f"""
    You are an expert Python developer.

    Your task is to generate or fix a Python script based on the user given task and the previous attempt scripts.

    USER GIVEN TASK: {state["task"]}
    Previous attempt scripts: {state.get("previous_script", [])[-MAX_SCRIPTS_IN_PROMPT:]}
    Last attempted script result: {state.get("result", "")[-MAX_RESULT_CHARS:]}

    If the previous attempt scripts are empty, generate a brand new script.
    Otherwise, fix the last script. Do NOT repeat a script that already failed.

    Environment rules:
    - The target machine is Windows.
    - Do NOT use wmic; it is removed on Windows 11.
    - Use PowerShell through subprocess for system information. Example:
      subprocess.run(
          ["powershell", "-NoProfile", "-NonInteractive", "-Command",
           "Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer, Model | ConvertTo-Json -Compress"],
          capture_output=True, text=True, timeout=20,
      )
    - For RAM use Win32_PhysicalMemory (sum the Capacity values).
    - For system brand use Win32_ComputerSystem (Manufacturer and Model).
    - For GPU use Win32_VideoController (Name and AdapterRAM).
    - Parse PowerShell JSON output with json.loads.
    - Always set a timeout on subprocess calls.
    - Print the final answer clearly.

    Rules:
    - Only return valid JSON
    - No explanations
    - No extra text
    - No preamble
    """


def _generate_script(state: PythonTaskState) -> dict:
    writer = get_stream_writer()
    writer(
        {
            "message": (
                "Generating Python script... "
                f"(attempt {state.get('attempt', 0) + 1}/{state.get('max_attempt', 1)})"
            )
        }
    )

    structured_llm = llm.with_structured_output(GeneratedScript)
    result: GeneratedScript = structured_llm.invoke(_script_prompt(state))

    return {
        "python_script": result.script,
        "previous_script": [result.script],
    }


def _execute_script(state: PythonTaskState) -> dict:
    writer = get_stream_writer()
    writer({"message": "Executing Python script..."})

    attempt = state.get("attempt", 0) + 1

    try:
        result = subprocess.run(
            [sys.executable, "-c", state["python_script"]],
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
            shell=False,
        )

        if result.returncode != 0:
            writer({"message": "Script execution failed."})
            return {
                "result": result.stderr[-MAX_RESULT_CHARS:],
                "status": "red",
                "attempt": attempt,
            }

        writer({"message": "Script completed."})
        output = result.stdout
        match = re.search(r"[A-Za-z]:\\[^\r\n]*", output)
        path = match.group(0).strip() if match else ""

        return {
            "result": output.strip()[-MAX_RESULT_CHARS:],
            "status": "green",
            "attempt": attempt,
            "output_file_path": path,
        }
    except subprocess.TimeoutExpired as exc:
        writer({"message": "Script timed out."})
        return {"result": str(exc), "status": "red", "attempt": attempt}
    except Exception as exc:
        writer({"message": str(exc)})
        return {"result": str(exc), "status": "red", "attempt": attempt}


def _evaluate_result(state: PythonTaskState) -> str:
    writer = get_stream_writer()
    writer({"message": "Evaluating Python script..."})

    if state["status"] == "green":
        return "success"
    if state.get("attempt", 0) >= state.get("max_attempt", 1):
        return "exhausted"
    return "retry"


def _build_graph():
    workflow = StateGraph(PythonTaskState)
    workflow.add_node("generate_script", _generate_script)
    workflow.add_node("execute_script", _execute_script)

    workflow.add_edge(START, "generate_script")
    workflow.add_edge("generate_script", "execute_script")
    workflow.add_conditional_edges(
        "execute_script",
        _evaluate_result,
        {"success": END, "retry": "generate_script", "exhausted": END},
    )

    return workflow.compile()


def execute_python_task(
    task: str,
    runtime: ToolRuntime,
    max_attempt: int = DEFAULT_MAX_ATTEMPTS,
) -> dict | str:
    """Generate and execute a Python script for the requested task.

    Args:
        task: The task to complete with a Python script.
        max_attempt: How many times the script may be generated and executed.
    """
    writer = get_stream_writer()
    chain = _build_graph()
    full_state = {}

    for chunk in chain.stream(
        {
            "task": task,
            "python_script": "",
            "result": "",
            "status": "",
            "previous_script": [],
            "attempt": 0,
            "max_attempt": max_attempt,
            "output_file_path": "",
        },
        stream_mode=["updates", "custom"],
        version="v2",
    ):
        if chunk["type"] == "updates":
            for node_state in chunk["data"].values():
                full_state.update(node_state)
        elif chunk["type"] == "custom":
            data = chunk["data"]
            message = (
                data
                if isinstance(data, str)
                else data.get("status") or data.get("message", "")
            )
            if message:
                writer({"message": str(message)})

    if full_state.get("status", "green") == "green":
        return {
            "result": full_state.get("result", ""),
            "output_file_path": full_state.get("output_file_path", ""),
        }

    return (
        f"Script still failing after {full_state.get('attempt', 0)} attempt(s):\n"
        f"{full_state.get('result', '')}\n\nFailing script:\n"
        f"{full_state.get('python_script', '')}"
    )
