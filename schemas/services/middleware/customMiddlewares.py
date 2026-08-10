from langchain.agents.middleware import (
    ModelRequest,
    ModelResponse,
    before_model,
    AgentState,
    wrap_model_call,
)
from langchain.messages import RemoveMessage
from langgraph.runtime import Runtime
from typing import Any, Callable
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from schemas.models.lang.chatGroq import complex_model, simple_model


@before_model(can_jump_to=["end"])
def welcome_back_message(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    messages = state.get("messages", [])

    if "user-rejoin" in messages[-1].content:
        return {
            # "messages": [AIMessage("")],
            "jump_to": "end",
        }
    return None


@wrap_model_call
async def dynamic_model_middleware(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    messages = request.state.get("messages", [])
    for msg in messages:
        if isinstance(msg.content, list):
            for content in msg.content:
                if content.get("type") == "text":
                    selected_model = simple_model
                else:
                    selected_model = complex_model

    return await handler(request.override(model=selected_model))


@before_model
def trim_joined_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    messages = state.get("messages", [])

    if len(messages) <= 2:
        return None

    if "user-rejoin" in messages[-1].content:
        new_messages = messages[:-2]
        return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)] + new_messages}

    return None
