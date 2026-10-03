from langchain.agents.middleware import (
    ModelRequest,
    ModelResponse,
    before_model,
    AgentState,
    wrap_model_call,
    FilesystemFileSearchMiddleware,
    AgentMiddleware,
)
from pathlib import Path
import os
from langchain.messages import RemoveMessage, ToolMessage
from langgraph.runtime import Runtime
from typing import Any, Callable
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.prebuilt.tool_node import ToolCallRequest
from ollama import chat
from schemas.models.lang.chatModels import complex_model, simple_model, local


class FlexibleFileSearchMiddleware(FilesystemFileSearchMiddleware):
    def _resolve_user_dir(self, name: str):
        profile = os.environ.get("USERPROFILE", str(Path.home()))
        for parent in (Path(profile) / "OneDrive", Path(profile)):
            candidate = parent / name
            if candidate.exists():
                return candidate.resolve()
        return None

    def _validate_and_resolve_path(self, path):
        if Path(path).is_absolute():
            return Path(path).resolve()

        normal = path.replace("/", "\\")
        parts = normal.split("\\")

        if parts and parts[0]:
            base = self._resolve_user_dir(parts[0])
            if base is not None:
                full = base.joinpath(*parts[1:]) if len(parts) > 1 else base
                return full.resolve()

        candidate = Path.home() / path
        if candidate.exists():
            return candidate.resolve()

        return super()._validate_and_resolve_path(path)


class RecursiveGlobMiddleware(AgentMiddleware):
    MAX_RESULTS = 200
    MAX_CHARS = 8000

    @staticmethod
    def _cap_result(result: str) -> str:
        lines = result.splitlines() if isinstance(result, str) else []
        if len(lines) > RecursiveGlobMiddleware.MAX_RESULTS:
            lines = lines[: RecursiveGlobMiddleware.MAX_RESULTS]
            lines.append(
                f"... ({len(lines)} of {len(result.splitlines())} matches shown, "
                "truncated to avoid overflowing context) ..."
            )
            result = "\n".join(lines)
        if isinstance(result, str) and len(result) > RecursiveGlobMiddleware.MAX_CHARS:
            result = (
                result[: RecursiveGlobMiddleware.MAX_CHARS]
                + "\n... (result truncated to avoid overflowing context) ..."
            )
        return result

    async def awrap_tool_call(self, request: ToolCallRequest, handler):
        call = request.tool_call
        if call["name"] == "glob_search":
            args = dict(call["args"])
            pattern = args.get("pattern", "")
            if pattern and "/" not in pattern and "**" not in pattern:
                args["pattern"] = f"**/{pattern}"
                request = request.override(tool_call={**call, "args": args})
        result = await handler(request)
        if call["name"] in {"glob_search", "grep_search"} and isinstance(result, ToolMessage):
            if isinstance(result.content, str):
                result = result.model_copy(update={"content": self._cap_result(result.content)})
        return result


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
def generate_chat_title(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    messages = state.get("messages", [])
    lastMessage = messages[len(messages) - 1].content
    if len(messages) <= 1:
        writer = runtime.stream_writer
        writer({"message": "Generating title to the chat"})
        response = chat(
            model="qwen2.5-coder:3b",
            messages=[
                {
                    "role": "user",
                    "content": f"generate creative short title for the chat based on message. no preamble:  The message: {lastMessage}",
                }
            ],
        )
        writer({"title": response.message.content})

    return None


@wrap_model_call
async def dynamic_model_middleware(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    try:
        selected_model = local
        messages = request.state.get("messages", [])
        for msg in messages[len(messages) - 1].content:
            if isinstance(msg, str):
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
