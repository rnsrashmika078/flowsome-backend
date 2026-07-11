from langchain.agents.middleware import before_model, after_model, AgentState
from langchain.messages import AIMessage
from langgraph.runtime import Runtime
from typing import Any


@before_model(can_jump_to=["end"])
def welcome_back_message(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    if "user-rejoin" in state["messages"][-1].content:
        return {
            # "messages": [AIMessage("")],
            "jump_to": "end",
        }
    return None
