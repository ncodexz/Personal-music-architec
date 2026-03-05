
from langgraph.graph import StateGraph, END
from core.graph.nodes.strategy_node import strategy_node
from core.graph.nodes.validation_node import validation_node
from core.graph.nodes.composition_node import composition_node
from core.graph.nodes.execution_node import execution_node
from core.graph.state import MusicState


def build_music_graph(repo, sp, llm, semantic_service):

    graph = StateGraph(MusicState)

    # =====================================================
    # Dependency Wrappers
    # =====================================================

    def strategy_wrapper(state):
        return strategy_node(state, llm)

    def composition_wrapper(state):
        return composition_node(state, repo, semantic_service)

    def execution_wrapper(state):
        return execution_node(state, sp, repo)
    

    # =====================================================
    # Nodes
    # =====================================================
    
    graph.add_node("strategy", strategy_wrapper)
    graph.add_node("validation", validation_node)
    graph.add_node("composition", composition_wrapper)
    graph.add_node("execution", execution_wrapper)

    # =====================================================
    # Entry Point
    # =====================================================

    graph.set_entry_point("strategy")


    # =====================================================
    # Strategy → Validation
    # =====================================================

    graph.add_edge("strategy", "validation")

    graph.add_conditional_edges(
        "validation",
        lambda state: "clarify" if state["needs_clarification"] else "compose",
        {
            "clarify": END,
            "compose": "composition",
        },
    )

    # =====================================================
    # Composition → Execution (direct, no confirmation)
    # =====================================================

    graph.add_conditional_edges(
        "composition",
        lambda state: (
            "end"
            if (state.get("strategy") or {}).get("goal") == "info"
            else "clarify"
            if state["needs_clarification"]
            else "execute"
        ),
        {
            "end": END,
            "clarify": END,
            "execute": "execution",
        },
    )

    # =====================================================
    # Execution → END
    # =====================================================

    graph.add_edge("execution", END)

    return graph.compile()