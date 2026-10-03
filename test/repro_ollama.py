import ollama

model = "gemma4:e2b"

messages = [
    {
        "role": "system",
        "content": (
            "You are a helpful assistant! When the user mentions a file or folder by name, "
            "pass its full path as the `path` argument to glob_search / grep_search. "
            "You run on the user's Windows computer and have FULL local filesystem access "
            "through glob_search and grep_search. Never claim you cannot access the local "
            "computer. To check whether software is installed (e.g. unreal engine), list "
            "likely install locations with glob_search and report what you actually find."
        ),
    },
    {"role": "user", "content": "check weather steam install or not ?"},
    {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "type": "function",
                "id": "8616cf11-a170-4c2a-aa85-144d81288430",
                "function": {
                    "name": "glob_search",
                    "arguments": {
                        "path": "C:/Program Files",
                        "pattern": "Steam*",
                    },
                },
            }
        ],
    },
    {
        "role": "tool",
        "tool_call_id": "8616cf11-a170-4c2a-aa85-144d81288430",
        "content": (
            "/Program Files\\PostgreSQL\\18\\pgAdmin 4\\python\\Lib\\site-packages\\pyotp\\contrib\\steam.py"
        ),
    },
]

res = ollama.chat(model=model, messages=messages, stream=False)
print("FINAL CONTENT:")
print(res["message"]["content"])