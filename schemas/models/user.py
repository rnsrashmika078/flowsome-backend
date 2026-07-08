from typing import Any
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from pydantic import BaseModel


class UserResponse(BaseModel):
    message: BaseMessage
