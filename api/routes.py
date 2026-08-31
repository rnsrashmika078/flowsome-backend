from pathlib import Path
from fastapi import Request, APIRouter, Depends, UploadFile, File
from langchain_core.messages import HumanMessage, ToolMessage
from fastapi.responses import StreamingResponse
from langchain_protocol import Command
from pydantic import BaseModel
import json
from sqlalchemy.orm import Session
import requests
from models.thread import Thread
from utils.helper import ImageEncode, clean_object, clean_object_v2, init_create_agent
from langgraph.config import get_stream_writer
from database.index import get_db

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

        file_content = None
        text_content = None
        response_file = None
        encoded_img = None

        for i in messages:
            if i == "None":
                continue
            elif len(messages) > 1:
                file_content = messages[1].get("content", "")
                text_content = messages[0].get("content", "")
            else:
                text_content = messages[0].get("content", "")

        # print(f"File content: {file_content}")
        # print(f"Text Content: {text_content}")

        # messages [{'type': 'human', 'content': 'whats up today'}, {}]

        # thread configurations
        config = {
            "configurable": {
                "thread_id": thread_id,
            },
            "recursion_limit": 25,
        }

        #  image encode
        encoded_img = ImageEncode(file_content, requests)

        # human in the loop
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
                    "raw": file_content,
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
            content = with_attachment if file_content else without_attachment

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
                    formatted_data = clean_object_v2(data)
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


@router.get("/api/threads/history/{thread}")
async def getHistory(request: Request, thread: str):
    config = {"configurable": {"thread_id": thread}}
    agent = request.app.state.agent

    state = await agent.aget_state(config)

    if not state:
        return {"messages": []}

    return {"values": state.values.get("messages", [])}


class ThreadBody(BaseModel):
    thread_id: str
    thread_name: str


@router.post("/api/threads/add_thread")
async def addThread(
    thread: ThreadBody, request: Request, db: Session = Depends(get_db)
):
    try:
        new_thread = Thread(thread_id=thread.thread_id, thread_name=thread.thread_name)
        db.add(new_thread)
        db.commit()
        db.refresh(new_thread)
        return {"thread": new_thread}
    except Exception as e:
        db.rollback()
        print(str(e))


@router.get("/api/threads/get_threads")
async def getThreads(db: Session = Depends(get_db)):
    try:
        threads = db.query(Thread).all()
        print(f"threads {threads}")
        return threads
    except Exception as e:
        db.rollback()
        print(str(e))


@router.delete("/api/thread/{thread}")
async def delete_thread(request: Request, thread: str, db: Session = Depends(get_db)):
    agent = request.app.state.agent
    await agent.checkpointer.adelete_thread(thread)
    found_thread = db.query(Thread).filter(Thread.thread_id == thread).first()

    if found_thread:
        db.delete(found_thread)
        db.commit()
    return {"message": "Thread was deleted!"}


@router.post("/select-folder")
async def select_folder(request: Request):
    request.app.state.root_path = r"C:\Users\Rashm\OneDrive\Desktop\path2"

    # request.app.state.agent = init_create_agent(request.app.state.checkpointer, app.state.root_path)
    return {"root_path": request.app.state.root_path}


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
