from langchain_ollama import ChatOllama

CHAT_MODEL = "gemma4:e2b"
SUMMARY_MODEL = "qwen2.5-coder:3b"
CODING_MODEL = "rafw007/gemma4-e4b-claude-coder:latest"

chat_model = ChatOllama(model=CHAT_MODEL, reasoning=True, num_ctx=16384)
summarize_model = ChatOllama(model=SUMMARY_MODEL, reasoning=False)
