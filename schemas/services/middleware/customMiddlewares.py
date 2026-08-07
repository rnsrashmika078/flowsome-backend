from langchain.agents.middleware import (
    before_model,
    AgentState,
    wrap_model_call,
)
from langchain.messages import RemoveMessage
from langgraph.runtime import Runtime
from typing import Any
from langgraph.graph.message import REMOVE_ALL_MESSAGES


@before_model(can_jump_to=["end"])
def welcome_back_message(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    messages = state.get("messages", [])

    if "user-rejoin" in messages[-1].content:
        return {
            # "messages": [AIMessage("")],
            "jump_to": "end",
        }
    return None


@before_model
def trim_joined_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    messages = state.get("messages", [])

    if len(messages) <= 2:
        return None

    if "user-rejoin" in messages[-1].content:
        new_messages = messages[:-2]
        return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)] + new_messages}

    return None

