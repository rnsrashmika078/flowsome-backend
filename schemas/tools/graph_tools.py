import json
import operator
import subprocess
from typing import Annotated, Literal, Optional
import os
import re

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.tools import tool
from langchain.tools import ToolRuntime
from langgraph.config import get_stream_writer, get_config

# from IPython.display import Image, display
from langchain_ollama import ChatOllama

# from model import CustomState
from pydantic import BaseModel, Field

# from utils.read_files import recall_project_structure

llm = ChatOllama(model="gemma4:e2b", reasoning=False, temperature=0.4)
import sys

MAX_RESULT_CHARS = 2000
MAX_SCRIPTS_IN_PROMPT = 2


# Graph state
class State(TypedDict):
    task: str
    python_script: str
    result: str
    status: str
    previous_script: Annotated[list[str], operator.add]
    attempt: int
    max_attempt: int
    output_file_path: str


class GeneratePythonScriptOutput(BaseModel):
    script: str = Field(..., description="Python script for user given task")


# Nodes
def generate_script(
    state: State,
) -> dict:
    """Generate python script based on user given task

    output:
        python_script: newly generated python script
        previous_script: previous attempts python scripts if there any
    """

    writer = get_stream_writer()
    writer(
        {
            "message": f"Generating Python script... (attempt {state.get('attempt', 0) + 1}/{state.get('max_attempt', 1)})"
        }
    )
    prompt = f"""
    You are an expert Python developer.

    Your task is to generate or fix python script based on user given task and the previous attempts scripts

    USER GIVEN TASK: {state["task"]}
    Previous attempts scripts: {state.get("previous_script", [])[-MAX_SCRIPTS_IN_PROMPT:]}
    Last attempted script result: {state.get("result", "")[-MAX_RESULT_CHARS:]}

    If Previous attempts scripts empty then generate a brand new script,
    otherwise fix the last script. Do NOT repeat a script that already failed.
    Rules:
    - Only return valid JSON
    - No explanations
    - No extra text
    - No Preamble
    """

    structured_llm = llm.with_structured_output(GeneratePythonScriptOutput)
    result: GeneratePythonScriptOutput = structured_llm.invoke(prompt)
    # print("output_file_path: ", result.output_file_path)
    return {
        "python_script": result.script,
        "previous_script": [result.script],
    }


# Nodes
def execute_script(
    state: State,
) -> dict:
    """Execute python script"""

    writer = get_stream_writer()
    writer({"message": "Executing Python script..."})

    print(state["python_script"])

    attempt = state.get("attempt", 0) + 1

    try:
        result = subprocess.run(
            [sys.executable, "-c", state["python_script"]],
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
        )
        print("RESULT OF THE SCRIPT", result)
        if result.returncode != 0:
            writer({"message": "Script execution failed."})

            return {
                "result": result.stderr[-MAX_RESULT_CHARS:],
                "status": "red",
                "attempt": attempt,
            }

        writer({"message": "Script completed."})
        result = result.stdout
        match = re.search(r"[A-Za-z]:\\[^\r\n]*", result)
        path = match.group(0).strip() if match else ""
        return {
            "result": result.strip()[-MAX_RESULT_CHARS:],
            "status": "green",
            "attempt": attempt,
            "output_file_path": path,
        }

    except subprocess.TimeoutExpired as e:
        writer({"message": "Script timed out."})

        return {"result": str(e), "status": "red", "attempt": attempt}

    except Exception as e:
        writer({"message": str(e)})
        return {"result": str(e), "status": "red", "attempt": attempt}


# Nodes
def eval_output(
    state: State,
) -> str:
    """Evaluate output of the python script and decide whether to retry"""

    writer = get_stream_writer()
    writer({"message": "Evaluating Python script..."})

    if state["status"] == "green":
        return "green"

    if state.get("attempt", 0) >= state.get("max_attempt", 1):
        return "exhausted"

    return "red"
