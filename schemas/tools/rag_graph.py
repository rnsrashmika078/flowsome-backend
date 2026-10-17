from langchain.tools import ToolRuntime
from langgraph.graph import END, START, StateGraph
from schemas.tools.rag_graph_tools import (
    State,
    check_index,
    embedding_and_store,
    read_document,
    retrieve_result,
    route_index,
    split_to_chunk,
)
from langgraph.config import get_stream_writer, get_config


def rag_tool(
    question: str,
    document_path: str,
    # runtime: ToolRuntime[None, CustomState],
    runtime: ToolRuntime,
):
    """Langgraph for retrial augment generation ( RAG )

    Args:
        question (str): question user ask related to the document
        document_path (str): file path to the document

    """

    writer = get_stream_writer()

    workflow = StateGraph(State)
    workflow.add_node("check_index", check_index)
    workflow.add_node("read_document", read_document)
    workflow.add_node("split_to_chunk", split_to_chunk)
    workflow.add_node("embedding_and_store", embedding_and_store)
    workflow.add_node("retrieve_result", retrieve_result)

    workflow.add_edge(START, "check_index")
    workflow.add_conditional_edges(
        "check_index",
        route_index,
        {
            "read_document": "read_document",
            "retrieve_result": "retrieve_result",
        },
    )
    workflow.add_edge("read_document", "split_to_chunk")
    workflow.add_edge("split_to_chunk", "embedding_and_store")
    workflow.add_edge("embedding_and_store", "retrieve_result")
    workflow.add_edge("retrieve_result", END)

    chain = workflow.compile()
    full_state = {}

    for chunk in chain.stream(
        {
            "question": question,
            "document_path": document_path,
        },
        stream_mode=["updates", "custom"],
        version="v2",
    ):
        if chunk["type"] == "updates":
            for node_name, node_state in chunk["data"].items():
                # print(f"Node {node_name} updated: {node_state}")
                full_state.update(node_state)
        if chunk["type"] == "custom":
            data = chunk["data"]
            message = (
                data
                if isinstance(data, str)
                else data.get("status") or data.get("message", "")
            )
            if message:
                writer({"message": message})

    return {
        "context": full_state.get("context", "no context"),
    }
