from typing import Any

from langchain.agents.middleware import AgentState, before_model
from langgraph.runtime import Runtime
from ollama import chat

from agent.models import SUMMARY_MODEL


@before_model
def generate_chat_title(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    messages = state.get("messages", [])

    if not messages or len(messages) > 1:
        return None

    content = messages[-1].content

    if isinstance(content, list):
        text = " ".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    else:
        text = content or ""

    text = text.strip()[:500]

    if not text:
        return None

    response = chat(
        model=SUMMARY_MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    "Generate a short chat title of at most 4 words from the "
                    "message below. Reply with the title only - no quotes, no "
                    f"preamble.\n\nMessage: {text}"
                ),
            }
        ],
        options={"num_predict": 24, "temperature": 0.2},
    )

    title = (response.message.content or "").strip()
    title = title.splitlines()[0].strip() if title else ""
    if title.lower().startswith("title:"):
        title = title.split(":", 1)[1].strip()
    title = " ".join(title.strip("\"'").split()[:6])

    if title:
        runtime.stream_writer({"title": title})

    return None
