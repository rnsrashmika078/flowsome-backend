import ollama

model = "gemma3:latest"

big_result = "\n".join(
    f"/Program Files/Folder{i // 20}/sub{chr(92)}deep{chr(92)}file{i}.cpp" for i in range(1500)
)
print("result size chars:", len(big_result))

# Scenario A: full correct history (small enough)
print("\n=== A) FULL history (system+user+ai_call+tool) ===")
res = ollama.chat(
    model=model,
    messages=[
        {"role": "system", "content": "You are a helpful assistant. Answer concisely."},
        {"role": "user", "content": "check weather steam install or not ?"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "type": "function",
                    "id": "abc123",
                    "function": {
                        "name": "glob_search",
                        "arguments": {"path": "C:/Program Files", "pattern": "**/*steam*"},
                    },
                }
            ],
        },
        {"role": "tool", "tool_call_id": "abc123", "content": big_result[:2000]},
    ],
    options={"num_ctx": 8192},
)
print("ANSWER:", repr(res["message"]["content"][:400]))

# Scenario B: truncated history - simulate ollama dropping the start (human message gone)
print("\n=== B) TRUNCATED history (user question evicted by overflow) ===")
res = ollama.chat(
    model=model,
    messages=[
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "type": "function",
                    "id": "abc123",
                    "function": {
                        "name": "glob_search",
                        "arguments": {"path": "C:/Program Files", "pattern": "**/*steam*"},
                    },
                }
            ],
        },
        {"role": "tool", "tool_call_id": "abc123", "content": big_result},
    ],
    options={"num_ctx": 2048},
)
print("ANSWER:", repr(res["message"]["content"][:400]))