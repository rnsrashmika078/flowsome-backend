from langchain_groq import ChatGroq
from core.config import settings
from langchain_ollama import ChatOllama
from core.config import settings


simple_model = ChatGroq(
    api_key=settings.groq_api_key,
    model=settings.chat_model_text,
    temperature=0,
    max_tokens=None,
    # reasoning_format="parsed",
    timeout=None,
    max_retries=2,
)
complex_model = ChatGroq(
    api_key=settings.groq_api_key,
    model=settings.chat_model_file,
    temperature=0,
    reasoning_format="hidden",
    reasoning_effort="none",
    # reasoning_format="parsed",
    timeout=None,
    max_retries=2,
)

model = "gemma4:e2b"
local = ChatOllama(model=model, reasoning=True)
summarizeModel = ChatOllama(model="qwen2.5-coder:3b", reasoning=False)
