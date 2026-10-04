import json
import operator
import subprocess
from typing import Annotated, Literal
import os

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

llm = ChatOllama(model="qwen2.5-coder:3b", reasoning=False, temperature=0.4)
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


class GeneratePythonScriptOutput(BaseModel):
    script: str = Field(..., description="Python script for user given task")


# class FileContentStructuredOutput(BaseModel):
#     content: str = Field(..., description="Suitable file content to the file")


# class StandardReactProjectStructure(BaseModel):
#     knowledge_base: str = Field(
#         ...,
#         description="The knowledge you gain from read md file about react project standard structure",
#     )


# Nodes
def generate_script(
    state: State,
) -> dict:
    """Generate python script based on user given task"""

    writer = get_stream_writer()
    writer(
        {
            "status": f"Generating Python script... (attempt {state.get('attempt', 0) + 1}/{state.get('max_attempt', 1)})"
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
    print("Script: ", result.script)
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
    writer({"status": "Executing Python script..."})

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
        if result.returncode != 0:
            writer({"message": "Script execution failed."})

            return {
                "result": result.stderr[-MAX_RESULT_CHARS:],
                "status": "red",
                "attempt": attempt,
            }

        writer({"message": "Script completed."})

        return {
            "result": result.stdout.strip()[-MAX_RESULT_CHARS:],
            "status": "green",
            "attempt": attempt,
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
    writer({"status": "Evaluating Python script..."})

    if state["status"] == "green":
        return "green"

    if state.get("attempt", 0) >= state.get("max_attempt", 1):
        return "exhausted"

    return "red"


def determine_file_path(
    state: State,
) -> dict:
    """decide the suitable project absolute path and return a suitable absolute path/directory according to the task based on user given fileTree and knowledge. NO PREAMBLE"""

    writer = get_stream_writer()
    writer({"status": "Scanning project path ..."})
    prompt = f"""
    YOU ARE ABSOLUTE PATH FINDER
    You MUST return ONLY valid JSzzzzzON.

    Output format:
    {{"absolute_path": "string"}}
    Task:
    {state['task']}

    ROOT ABSOLUTE PATH : {state['root_path']}
    
    File Tree:
    {state['fileTree']}
    
    Knowledge about standard file tree:
    {state['knowledge_base']}

    Rules:
    - Only return JSON
    - Do NOT explain
    - Do NOT add extra text
    """

    structured_llm = llm.with_structured_output(FilePathStructuredOutput)
    result: FilePathStructuredOutput = structured_llm.invoke(prompt)
    print("STRUCTURED OUTPUT:", result)
    return {"absolute_path": result.absolute_path}


def isPathAvailable(state: State):
    """check weather the state path available"""

    writer = get_stream_writer()
    writer({"status": "Checking Path Availability..."})

    if state["absolute_path"] is None:
        return "Fail"
    return "Pass"


def isLoopDone(state: State):
    """check weather the loop done"""

    writer = get_stream_writer()
    writer({"status": "Checking re run loop state..."})

    if state["current_loop_count"] > state["loop_count"]:
        return "Done"
    cleanState()
    return "Continue"


def generate_file_content(
    state: State,
) -> dict:
    """generate file content according to the task"""

    writer = get_stream_writer()
    writer({"status": "Generating file content..."})
    prompt = f"""
    YOU ARE CONTENT GENERATOR
    Generate file content based on TASK
    You MUST return ONLY valid JSON.
    
     Output format:
    {{"content": "string"}}
    
    Task : {state['task']}
    
    Rules:
    - Only return JSON
    - Do NOT explain
    - GENERATE JUST CONTENT ONLY 
    """

    structured_llm = llm.with_structured_output(FileContentStructuredOutput)
    result: FileContentStructuredOutput = structured_llm.invoke(prompt)
    print("FILE CONTENT:", result)
    return {"content": result.content}


def generate_file(
    state: State,
) -> str:
    """use to create/generate file"""

    writer = get_stream_writer()
    writer({"status": "Generating file ..."})
    path = state["absolute_path"]
    content = state["content"]
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            writer({"status": "On Generating..."})
            f.write(content)
            count = state.get("current_loop_count", 1) + 1
            return {"task_status": "Success", "current_loop_count": count}
    except Exception as e:
        return {"task_status": "Failed"}


def run_langgraph(
    task: str,
    loop_count: int,
    runtime: ToolRuntime[None, CustomState],
) -> str:
    """Langgraph agent that work with the file system

    Args:
        task (str): Task user given to you
        loop_count: (int): How many times run this task

    Return :
     str:  Only successfully or failed message.
    """

    writer = get_stream_writer()

    workflow = StateGraph(State)
    workflow.add_node("recall_standard_structure", recall_standard_structure)
    workflow.add_node("determine_path", determine_file_path)
    workflow.add_node("content_generate", generate_file_content)
    workflow.add_node("file_generation", generate_file)

    # config = get_config()
    # runtime_state = config.get("configurable", {})
    # path = runtime_state.get("rootPath")

    tree = runtime.state.get("fileTree")
    root_path = runtime.state.get("rootPath")
    # path = runtime.state.get("rootPath")
    tree_str = json.dumps(tree, indent=2)

    if tree_str is None:
        return
    # workflow.add_edge(START, "recall_standard_structure")
    # workflow.add_edge("recall_standard_structure", END)
    workflow.add_edge(START, "recall_standard_structure")
    workflow.add_edge("recall_standard_structure", "determine_path")
    workflow.add_conditional_edges(
        "determine_path", isPathAvailable, {"Fail": END, "Pass": "content_generate"}
    )
    workflow.add_edge("content_generate", "file_generation")
    # workflow.add_edge("file_generation", END)
    workflow.add_conditional_edges(
        "file_generation",
        isLoopDone,
        {"Done": END, "Continue": "determine_path"},
    )

    chain = workflow.compile()
    full_state = {}

    for chunk in chain.stream(
        {
            "task": task,
            "root_path": root_path,
            "fileTree": tree_str,
            "absolute_path": None,
            "content": None,
            "knowledge_base": None,
            "task_status": None,
            "loop_count": loop_count,
            "current_loop_count": 1,
        },
        stream_mode=["updates", "custom"],
        version="v2",
    ):
        if chunk["type"] == "updates":
            for node_name, state in chunk["data"].items():
                # print(f"Node {node_name} updated: {state}")
                full_state.update(state)
        if chunk["type"] == "custom":
            # print(f"Status: {chunk['data']['status']}")
            writer(f"{chunk['data']['status']}")

    state = full_state
    # return {
    #     "absolute_path": state.get("absolute_path"),
    #     "content": state.get("content"),
    # }
    return f"file create successful at {state["absolute_path"]}"
