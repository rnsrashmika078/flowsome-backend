import base64
import json

import requests


def _is_json_safe(value) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, dict):
        return all(_is_json_safe(key) and _is_json_safe(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return all(_is_json_safe(item) for item in value)
    try:
        json.dumps(value)
        return True
    except (TypeError, ValueError):
        return False


def clean_for_stream(value):
    if hasattr(value, "model_dump"):
        return clean_for_stream(value.model_dump())
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key == "shell_session_resources":
                continue
            cleaned = clean_for_stream(item)
            if _is_json_safe(cleaned):
                result[key] = cleaned
        return result
    if isinstance(value, (list, tuple)):
        result = []
        for item in value:
            cleaned = clean_for_stream(item)
            if _is_json_safe(cleaned):
                result.append(cleaned)
        return result
    return value


def encode_image_url(url: str) -> str | None:
    if not url:
        return None
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return base64.b64encode(response.content).decode("utf-8")
