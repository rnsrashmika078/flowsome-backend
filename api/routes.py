from fastapi import Request, APIRouter, Depends
from schemas.models.user import UserResponse
from schemas.services.lang.chatGroq import get_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from fastapi.responses import StreamingResponse
from langchain_protocol import Command
from langchain.agents import AgentState, create_agent
import json


# path param : "/api/home/{id}"

router = APIRouter()


@router.get("/api/home")
async def home(request: Request):
    try:
        return {"name": "Rashmika"}
    except Exception as err:
        return {"error": str(err)}, 500


@router.post("/api/stream")
async def stream_response(request: Request, agent=Depends(get_agent)):
    try:
        body = await request.json()

        payload = body.get("input", body)
        thread_id = payload.get("threadId", "chat123")
        interrupt_response = payload.get("interruptResponse")

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
            messages = payload.get("messages", [])
            first_msg_content = messages[0].get("content", "") if messages else ""
            input_data = {"messages": [HumanMessage(content=first_msg_content)]}

        async def generate():
            try:
                async for stream_mode, data in agent.astream(
                    input_data,
                    config=config,
                    stream_mode=["updates", "messages", "values", "tools", "custom"],
                ):

                    def clean_object(obj):
                        if isinstance(obj, BaseMessage):
                            data = {
                                "type": obj.type,
                                "content": obj.content,
                                "id": getattr(obj, "id", None),
                                "additional_kwargs": getattr(
                                    obj, "additional_kwargs", {}
                                ),
                                "response_metadata": getattr(
                                    obj, "response_metadata", {}
                                ),
                            }
                            if isinstance(obj, ToolMessage):
                                data["tool_call_id"] = obj.tool_call_id
                                data["artifact"] = obj.artifact
                            if isinstance(obj, AIMessage):
                                data["tool_calls"] = obj.tool_calls
                            return data

                        elif hasattr(obj, "model_dump"):
                            return obj.model_dump()

                        elif isinstance(obj, dict):
                            return {k: clean_object(v) for k, v in obj.items()}
                        elif isinstance(obj, (list, tuple)):
                            return [clean_object(item) for item in obj]

                        return obj

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
                # "X-Accel-Buffering": "no",
            },
        )

    except Exception as err:
        return {"error": str(err)}, 500
