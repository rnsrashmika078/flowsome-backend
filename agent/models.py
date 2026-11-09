from langchain_ollama import ChatOllama

from config import settings

CHAT_MODEL = "gemma4:e2b"
SUMMARY_MODEL = "qwen2.5-coder:3b"
CODING_MODEL = "qwen2.5-coder:3b"

OLLAMA_BASE_URL = settings.OLLAMA_BASE_URL

chat_model = ChatOllama(model=CHAT_MODEL, reasoning=True, num_ctx=16384, base_url=OLLAMA_BASE_URL)
summarize_model = ChatOllama(model=SUMMARY_MODEL, reasoning=False, base_url=OLLAMA_BASE_URL)
