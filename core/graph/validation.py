from typing import Tuple, Optional


def validate_strategy(strategy: Optional[dict]) -> Tuple[bool, Optional[str]]:
    """
    Validate the generated strategy structure for unified contract.
    Returns:
        (is_valid, clarification_message)
    """

    if strategy is None:
        return False, "I could not understand your request. Could you clarify what you would like to do?"

    goal = strategy.get("goal")

    if goal not in ["build", "modify", "info"]:
        return False, "Invalid goal. Please specify a valid action."

    # =====================================================
    # INFO VALIDATION
    # =====================================================

    if goal == "info":

        info_type = strategy.get("info_type")

        if not info_type:
            return False, "Please specify what information you would like."

        return True, None

    target = strategy.get("target", {})
    sources = strategy.get("sources", [])
    modification = strategy.get("modification")
    constraints = strategy.get("constraints", {})

    # =====================================================
    # BUILD VALIDATION
    # =====================================================

    if goal == "build":

        if not isinstance(sources, list) or len(sources) == 0:
            return False, "To build a playlist, I need at least one source."

        for source in sources:
            source_type = source.get("type")

            if source_type not in [
                "artist",
                "album",
                "top_played",
                "recently_added",
                "explicit",
            ]:
                return False, f"Unsupported source type '{source_type}'."

        return True, None

    # =====================================================
    # MODIFY VALIDATION
    # =====================================================

    if goal == "modify":

        identifier = target.get("identifier")
        if not identifier or not isinstance(identifier, str):
            return False, "To modify a playlist, I need a valid playlist name."

        if not modification or not isinstance(modification, dict):
            return False, "Please specify what modification you would like to perform."

        action = modification.get("action")

        if action not in ["add", "delete", "rename", "adapt"]:
            return False, "Unsupported modification action."

        return True, None

    return False, "Invalid strategy structure."