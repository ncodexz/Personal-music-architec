from langgraph.graph import StateGraph, END

from core.graph.state import MusicState
from core.graph.nodes import (
    strategy_node,
    validation_node,
    composition_node,
    confirmation_node,
    execution_node,
)
from core.graph.intent import intent_node
from core.graph.info_queries import info_query_node


def build_music_graph(conn, sp, llm):

    graph = StateGraph(MusicState)

    # --- Wrappers to inject dependencies ---

    def intent_wrapper(state):
        return intent_node(state, llm)

    def strategy_wrapper(state):
        return strategy_node(state, llm)

    def composition_wrapper(state):
        return composition_node(state, conn)

    def execution_wrapper(state):
        return execution_node(state, sp)

    def info_wrapper(state):
        return info_query_node(state, conn)

    # --- Add nodes ---

    graph.add_node("intent", intent_wrapper)
    graph.add_node("strategy", strategy_wrapper)
    graph.add_node("validation", validation_node)
    graph.add_node("composition", composition_wrapper)
    graph.add_node("confirmation", confirmation_node)
    graph.add_node("execution", execution_wrapper)
    graph.add_node("info", info_wrapper)

    # --- Entry point ---

    graph.set_entry_point("intent")

    # --- Intent branching ---

    graph.add_conditional_edges(
        "intent",
        lambda state: state["intent"],
        {
            "build": "strategy",
            "info": "info",
            "unknown": END,
        },
    )

    # --- Info flow ends immediately ---

    graph.add_edge("info", END)

    # --- Build flow ---

    graph.add_edge("strategy", "validation")

    graph.add_conditional_edges(
        "validation",
        lambda state: "clarify" if state["needs_clarification"] else "compose",
        {
            "clarify": END,
            "compose": "composition",
        },
    )

    graph.add_conditional_edges(
        "composition",
        lambda state: "clarify" if state["needs_clarification"] else "confirm",
        {
            "clarify": END,
            "confirm": "confirmation",
        },
    )

    graph.add_edge("confirmation", END)
    graph.add_edge("execution", END)

    return graph.compile()