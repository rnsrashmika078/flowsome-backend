import asyncio
import json

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest
from langchain_core.messages import HumanMessage


async def main():
    import sys, os

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from utils.helper import init_create_agent
    from schemas.services.middleware.customMiddlewares import (
        FlexibleFileSearchMiddleware,
        RecursiveGlobMiddleware,
    )
    from langchain.agents.middleware import AgentMiddleware, AgentState
    from langgraph.runtime import Runtime
    from typing import Any, Callable

    from utils.helper import system_prompt
    from schemas.models.lang.chatModels import local

    class SpyMiddleware(AgentMiddleware):
        async def awrap_model_call(self, request: ModelRequest, handler: Callable):
            print("\n===== MODEL CALL #", getattr(self, "_n", 0), "=====")
            for m in request.messages:
                t = getattr(m, "type", "?")
                c = getattr(m, "content", None)
                if isinstance(c, list):
                    c = json.dumps(c)[:300]
                tc = getattr(m, "tool_calls", None)
                extra = f" tool_calls={tc}" if tc else ""
                print(f"  [{t}] {str(c)[:300]}{extra}")
            try:
                self._n += 1
            except AttributeError:
                self._n = 1
            return await handler(request)

    spy = SpyMiddleware()

    client = None
    # replicate tools from helper (glob/grep via middleware)
    agent = create_agent(
        model=local,
        system_prompt=system_prompt,
        middleware=[
            RecursiveGlobMiddleware(),
            FlexibleFileSearchMiddleware(
                root_path="C:/",
                use_ripgrep=True,
                max_file_size_mb=10,
            ),
            spy,
        ],
    )

    config = {"configurable": {"thread_id": "repro-steam"}}

    async for stream_mode, data in agent.astream(
        {"messages": [HumanMessage(content="check weather steam install or not ?")]},
        config=config,
        stream_mode=["updates", "messages", "values", "tools", "custom"],
    ):
        pass


asyncio.run(main())