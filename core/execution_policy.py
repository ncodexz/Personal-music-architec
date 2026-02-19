class ExecutionPolicy:

    LEVEL_1_TOOLS_WITH_CRITERIA = {
        "add_tracks_to_playlist_by_name",
        "remove_tracks_from_playlist_by_name",
        "create_mixed_playlist"
    }

    @staticmethod
    def validate(tool_name: str, arguments: dict) -> dict:

        if tool_name in ExecutionPolicy.LEVEL_1_TOOLS_WITH_CRITERIA:

            criteria = arguments.get("criteria", {})

            if not criteria:
                return {
                    "valid": False,
                    "message": "Selection criteria is required."
                }

            if "artists" in criteria and "artist_limits" not in criteria:
                return {
                    "valid": False,
                    "message": "You must specify how many songs per artist."
                }

        return {"valid": True}
