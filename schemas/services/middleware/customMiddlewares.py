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
from schemas.models.lang.chatModels import complex_model, simple_model, local




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
    try:
        selected_model = local
        messages = request.state.get("messages", [])
        for msg in messages[len(messages)-1].content:
            if(isinstance(msg,str)):
                continue
            if msg.get("type") != "text":
                        print("I AM SWITCH TO MULTI MODEL")
                        selected_model = complex_model

        return await handler(request.override(model=selected_model))
    except Exception as e:
        print(f"Middleware error {e}")


@wrap_model_call
async def change_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    selected_model = local
    messages = request.state.get("messages", [])
    for msg in messages:
        if isinstance(msg.content, list):
            for content in msg.content:
                if content.get("type") != "text":
                    print("I AM SWITCH TO MULTI MODEL")
                    selected_model = complex_model
                else:
                    print("I AM SWITCH TO SINGLE MODEL")

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
