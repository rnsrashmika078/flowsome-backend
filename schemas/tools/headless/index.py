from langchain.tools import tool

@tool
def get_device_info(query: str) -> str:
    """Get headless device diagnostics or status info."""
    return f"Status for {query}: active"
