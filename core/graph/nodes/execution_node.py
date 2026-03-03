from core.graph.state import MusicState
from core.graph.execution.handler import execute_build, execute_modify


def execution_node(state: MusicState, sp, repo) -> MusicState:
    """
    Graph execution node.
    Delegates real execution logic to execution handlers.
    """

    strategy = state.get("strategy")
    goal = strategy.get("goal") if strategy else None

    if not strategy:
        state["error"] = "No valid strategy found."
        state["needs_clarification"] = False
        return state

    if goal == "build":
        return execute_build(state, sp)

    if goal == "modify":
        return execute_modify(state, sp, repo)

    state["error"] = "Unsupported goal."
    state["needs_clarification"] = False
    return state