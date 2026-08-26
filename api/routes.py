import base64
from pathlib import Path
from fastapi import Request, APIRouter, Depends, UploadFile, File
from langchain_core.messages import HumanMessage, ToolMessage
from fastapi.responses import StreamingResponse
from langchain_protocol import Command
from pydantic import BaseModel
import json

import requests
from utils.helper import clean_object
from langgraph.config import get_stream_writer
import uuid
import os

router = APIRouter()


@router.post("/api/stream")
async def stream_response(request: Request):
    try:

        # writer = get_stream_writer();
        body = await request.json()
        payload = body.get("input", body)
        thread_id = payload.get("threadId", "1235")
        interrupt_response = payload.get("interruptResponse")
        messages = payload.get("messages", [])

        file_content = ""
        text_content = ""
        for i in messages:
            if i is "None":
                continue
            elif len(messages) > 1:
                file_content = messages[1].get("content", "")
                text_content = messages[0].get("content", "")
            else:
                text_content = messages[0].get("content", "")

        print(f"File content: {file_content}")
        print(f"Text Content: {text_content}")

        # messages [{'type': 'human', 'content': 'whats up today'}, {}]

        config = {
            "configurable": {
                "thread_id": thread_id,
            },
            "recursion_limit": 25,
        }
        # path  = rf"{file_content}"
        # You can also pass in base64 encoded image data
        response_file = requests.get(file_content)
        image_bytes = response_file.content
        
        encoded_img = base64.b64encode(image_bytes).decode("utf-8")
        if interrupt_response:
            input_data = Command(
                resume={"decisions": interrupt_response.get("decisions")}
            )
        else:
            with_attachment = [
                {"type": "text", "text": text_content},
                {
                    "type": "image_url",
                    "image_url": {"url": encoded_img},
                },
                #     {
                #         "type": "image_url",
                #         "image_url": {
                #             "url": file_content,
                #         },
                #     },
            ]

            without_attachment = [
                {"type": "text", "text": text_content},
            ]
            # content = with_attachment if file_content else without_attachment
            content = with_attachment 

            input_data = {
                "messages": [
                    HumanMessage(content=content),
                ]
            }

        agent = request.app.state.agent

        async def generate():
            try:
                async for stream_mode, data in agent.astream(
                    input_data,
                    config=config,
                    stream_mode=[
                        "updates",
                        "messages",
                        "values",
                        "tools",
                        "custom",
                    ],
                ):
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
async def getHistory(request: Request, thread: int):
    config = {"configurable": {"thread_id": thread}}
    agent = request.app.state.agent

    state = await agent.aget_state(config)

    if not state:
        return {"messages": []}

    return {"values": state.values.get("messages", [])}


@router.delete("/api/thread")
async def clear_history(request: Request):
    threadList = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    agent = request.app.state.agent

    for i in threadList:
        await agent.checkpointer.adelete_thread(i)

    return {"message": "Thread history deleted"}


# upload directory

# UPLOAD_DIR = "uploads"
# os.makedirs(UPLOAD_DIR, exist_ok=True)


# @router.post("/local-upload")
# async def upload_image(file: UploadFile = File(None)):
#     print(f"FILE {file}")
#     filename = f"{uuid.uuid4()}_{file.filename}"
#     path = os.path.join(UPLOAD_DIR, filename)

#     with open(path, "wb") as f:
#         f.write(await file.read())

#     return {"url": f"http://localhost:8000/uploads/{filename}"}
