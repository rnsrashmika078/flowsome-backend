from langchain.tools import tool
import os

from langchain_protocol import Command

@tool("read_file")  # Custom name
def read_file_tool(path_to_file: str) -> str:
    """read file from user computer.
    
    input: filePath: path to the file -> "document/name/txt"

    """
    
    home_dir = os.path.expanduser("~");
    file_path = os.path.join(home_dir,path_to_file);
    
    with open(file_path, "r" , encoding="utf-8") as file:
        content = file.read()
        # return {
        #     "filePath" : file_path,
        #     "Content" : content
        # }
        return f"Content: {content}"