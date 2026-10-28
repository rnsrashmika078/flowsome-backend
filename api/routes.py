import json
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langchain_protocol import Command
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agent.serialization import clean_for_stream, encode_image_url
from database.models import Thread
from database.session import get_db

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@router.post("/api/stream")
async def stream_response(request: Request):
    try:
        body = await request.json()
        payload = body.get("input", body)
        thread_id = payload.get("threadId", "1235")
        interrupt_response = payload.get("interruptResponse")
        messages = payload.get("messages", [])

        file_content = None
        text_content = ""

        for message in messages:
            if message == "None":
                continue
            if len(messages) > 1:
                file_content = messages[1].get("content", "")
                text_content = messages[0].get("content", "")
            else:
                text_content = messages[0].get("content", "")

        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 25,
        }

        if interrupt_response:
            input_data = Command(
                resume={"decisions": interrupt_response.get("decisions")}
            )
        else:
            content = [{"type": "text", "text": text_content}]
            if file_content:
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": encode_image_url(file_content)},
                        "raw": file_content,
                    }
                )
            input_data = {"messages": [HumanMessage(content=content)]}

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
                    yield f"event: {stream_mode}\n"
                    yield f"data: {json.dumps(clean_for_stream(data))}\n\n"
            except Exception as exc:
                yield "event: error\n"
                yield f"data: {json.dumps({'error': str(exc)})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except Exception as exc:
        return {"error": str(exc)}, 500


@router.get("/api/threads/history/{thread}")
async def get_history(request: Request, thread: str):
    config = {"configurable": {"thread_id": thread}}
    state = await request.app.state.agent.aget_state(config)

    if not state:
        return {"messages": []}

    return {"values": state.values.get("messages", [])}


class ThreadBody(BaseModel):
    thread_id: str
    thread_name: str


@router.post("/api/threads/add_thread")
async def add_thread(thread: ThreadBody, db: Session = Depends(get_db)):
    try:
        new_thread = Thread(
            thread_id=thread.thread_id,
            thread_name=thread.thread_name,
        )
        db.add(new_thread)
        db.commit()
        db.refresh(new_thread)
        return {"thread": new_thread}
    except Exception as exc:
        db.rollback()
        return {"error": str(exc)}, 500


@router.get("/api/threads/get_threads")
async def get_threads(db: Session = Depends(get_db)):
    return db.query(Thread).all()


@router.delete("/api/thread/{thread}")
async def delete_thread(
    request: Request,
    thread: str,
    db: Session = Depends(get_db),
):
    await request.app.state.agent.checkpointer.adelete_thread(thread)

    found_thread = db.query(Thread).filter(Thread.thread_id == thread).first()
    if found_thread:
        db.delete(found_thread)
        db.commit()

    return {"message": "Thread was deleted!"}


@router.post("/api/upload")
async def upload_image(request: Request, file: UploadFile = File(...)):
    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    filename = f"{uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "secure_url": str(request.base_url).rstrip("/") + f"/uploads/{filename}"
    }
