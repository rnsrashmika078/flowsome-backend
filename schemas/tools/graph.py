from langchain.tools import ToolRuntime
from langgraph.graph import END, START, StateGraph
from schemas.tools.graph_tools import (
    State,
    eval_output,
    execute_script,
    generate_script,
    isPathAvailable,
)
from langgraph.config import get_stream_writer, get_config


def execute_python_task(
    task: str,
    # runtime: ToolRuntime[None, CustomState],
    runtime: ToolRuntime,
    max_attempt: int = 3,
) -> str:
    """Langgraph agent for generate python script based on user given task

    Args:
        task (str): Task user given to you to make python script
        max_attempt: (int): How many times the script may be generated and executed

    Return :
     str: Output produced by the executed script, or the error and the
          failing script when it could not be executed.
    """

    writer = get_stream_writer()

    workflow = StateGraph(State)
    workflow.add_node("generate_python_script", generate_script)
    workflow.add_node("execute_python_script", execute_script)

    workflow.add_edge(START, "generate_python_script")
    workflow.add_edge("generate_python_script", "execute_python_script")

    workflow.add_conditional_edges(
        "execute_python_script",
        eval_output,
        {"green": END, "red": "generate_python_script", "exhausted": END},
    )
    # workflow.add_edge("execute_python_script", END)

    chain = workflow.compile()
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
        },
        stream_mode=["updates", "custom"],
        version="v2",
    ):
        if chunk["type"] == "updates":
            for node_name, node_state in chunk["data"].items():
                # print(f"Node {node_name} updated: {node_state}")
                full_state.update(node_state)
        if chunk["type"] == "custom":
            data = chunk["data"]
            message = (
                data
                if isinstance(data, str)
                else data.get("status") or data.get("message", "")
            )
            if message:
                writer(str(message))

    script = full_state.get("python_script", "")
    result = full_state.get("result", "")
    attempts = full_state.get("attempt", 0)

    if full_state.get("status", "green") == "green":
        return result or "Script completed successfully with no output."

    return (
        f"Script still failing after {attempts} attempt(s):\n{result}"
        f"\n\nFailing script:\n{script}"
    )
