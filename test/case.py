from langchain.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.messages import BaseMessage
from utils.helper import clean_object

messages = [
    HumanMessage(content="Hello AI", id="msg1"),
    AIMessage(
        content="Hello, how can I help?",
        id="msg2",
        tool_calls=[{"name": "search", "args": {"query": "weather"}, "id": "call1"}],
    ),
    ToolMessage(
        content="Weather is sunny", tool_call_id="call1", artifact={"temperature": 30}
    ),
]
# result = clean_object(messages)
message_2 = HumanMessage(content="Hello AI", id="msg1")
message_3 = ToolMessage(
    content="Weather is sunny", tool_call_id="call1", artifact={"temperature": 30}
)
obj = {"name": "rashmika"}
# print(isinstance(message_3, ToolMessage))
# print(type(messages))
# print(type(message_2))
# print(type(message_3))
# print(isinstance(message_2, BaseMessage))
print(hasattr(message_2, "model_dump"))
print(isinstance(message_2, dict))
print(obj.items())
