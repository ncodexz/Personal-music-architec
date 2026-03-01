def build_music_graph(repo, sp, llm):

    graph = StateGraph(MusicState)

    # =====================================================
    # Dependency Wrappers
    # =====================================================

    def intent_wrapper(state):
        return intent_node(state, llm)

    def strategy_wrapper(state):
        return strategy_node(state, llm)

    def composition_wrapper(state):
        return composition_node(state, repo)

    def execution_wrapper(state):
        return execution_node(state, sp)

    # =====================================================
    # Nodes
    # =====================================================

    graph.add_node("intent", intent_wrapper)
    graph.add_node("strategy", strategy_wrapper)
    graph.add_node("validation", validation_node)
    graph.add_node("composition", composition_wrapper)
    graph.add_node("execution", execution_wrapper)

    # =====================================================
    # Entry Point
    # =====================================================

    graph.set_entry_point("intent")

    # =====================================================
    # Intent Routing
    # =====================================================

    graph.add_conditional_edges(
        "intent",
        lambda state: state["intent"],
        {
            "build": "strategy",
            "modify": "strategy",
            "info": "strategy",
            "unknown": END,
        },
    )

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
            if state.get("strategy", {}).get("goal") == "info"
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