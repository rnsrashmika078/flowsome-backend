import ollama

model = "gemma3:latest"

big_result = "\n".join(
    f"/Program Files/Folder{i // 20}/sub{chr(92)}deep{chr(92)}file{i}.cpp" for i in range(2500)
)
print("result size chars:", len(big_result))

messages = [
    {
        "role": "system",
        "content": (
            "You are a helpful assistant. When the user asks whether a program is installed "
            "you check with glob_search and answer yes/no. Do not repeat the tool schema."
        ),
    },
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
    {"role": "tool", "tool_call_id": "abc123", "content": big_result},
]

for nctx in (8192, 2048):
    print(f"\n=== num_ctx={nctx} prompt tokens approx = {len(messages[3]['content'])//4} ===")
    try:
        res = ollama.chat(model=model, messages=messages, stream=False, options={"num_ctx": nctx})
        print("ANSWER:", repr(res["message"]["content"][:300]))
    except Exception as e:
        print("ERR:", type(e).__name__, e)