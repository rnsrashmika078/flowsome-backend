from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage


def clean_object(obj):
    if isinstance(obj, BaseMessage):
        data = {
            "type": obj.type,
            "content": obj.content,
            "id": getattr(obj, "id", None),
            "additional_kwargs": getattr(obj, "additional_kwargs", {}),
            "response_metadata": getattr(obj, "response_metadata", {}),
            "usage_metadata": getattr(obj, "usage_metadata", {}),
        }
        if isinstance(obj, ToolMessage):
            data["tool_call_id"] = obj.tool_call_id
            data["artifact"] = obj.artifact
        if isinstance(obj, AIMessage):
            data["tool_calls"] = obj.tool_calls
        return data

    elif hasattr(obj, "model_dump"):  # check for pydantic model or nt
        return obj.model_dump()

    elif isinstance(obj, dict):
        return {k: clean_object(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [clean_object(item) for item in obj]

    return obj


# def clean_object(obj):
#     if isinstance(obj, BaseMessage):
#         return obj
