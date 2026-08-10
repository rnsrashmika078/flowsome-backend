from fastapi import Request, APIRouter, Depends
from schemas.models.lang.chatGroq import get_agent
from langchain_core.messages import HumanMessage, ToolMessage
from fastapi.responses import StreamingResponse
from langchain_protocol import Command
from pydantic import BaseModel
import json
from utils.helper import clean_object

router = APIRouter()


@router.post("/api/stream")
async def stream_response(request: Request, agent=Depends(get_agent)):
    try:
        body = await request.json()
        payload = body.get("input", body)
        thread_id = payload.get("threadId", "1235")
        interrupt_response = payload.get("interruptResponse")
        messages = payload.get("messages", [])

        file_content = ""
        text_content = ""
        for i in messages:
            if type(i) is "None":
                continue
            elif len(messages) > 1:
                file_content = messages[1].get("url", "")
                text_content = messages[0].get("content", "")
            else:
                text_content = messages[0].get("content", "")

        print("PAYLOAD", payload)
        print("file_content", file_content)
        print("text_content", text_content)
        print("text_content", type(text_content))
        print("messages", messages)

        # messages [{'type': 'human', 'content': 'whats up today'}, {}]

        config = {
            "configurable": {
                "thread_id": thread_id,
            },
            "recursion_limit": 25,
        }

        if interrupt_response:
            input_data = Command(
                resume={"decisions": interrupt_response.get("decisions")}
            )
        else:
            with_attachment = [
                {"type": "text", "text": text_content},
                {
                    "type": "image_url",
                    "image_url": {"url": file_content},
                },
            ]
            without_attachment = [
                {"type": "text", "text": text_content},
            ]

            content = with_attachment if file_content else without_attachment
            input_data = {
                "messages": [
                    HumanMessage(content=content),
                ]
            }

        async def generate():
            try:
                async for stream_mode, data in agent.astream(
                    input_data,
                    config=config,
                    stream_mode=[
                        # "updates",
                        "messages",
                        "values",
                        "tools",
                        "custom",
                    ],
                ):
                    # print(data)
                    formatted_data = clean_object(data)

                    yield f"event: {stream_mode}\n"
                    yield f"data: {json.dumps(formatted_data)}\n\n"

            except Exception as e:
                yield f"event: error\n"
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except Exception as err:
        print(str(err))
        return {"error": str(err)}, 500


class History(BaseModel):
    thread: str


@router.get("/api/threads/{thread}")
async def getHistory(thread: int, agent=Depends(get_agent)):
    config = {"configurable": {"thread_id": thread}}

    state = await agent.aget_state(config)

    if not state:
        return {"messages": []}

    return {"values": state.values.get("messages", [])}
