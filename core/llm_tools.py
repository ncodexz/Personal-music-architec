"""
LLM Tool Definitions – Level 1 Closed

Level 1 is strictly deterministic.

Rules:
- Do NOT assume defaults.
- Do NOT invent selection criteria.
- If the user's selection logic is unclear or incomplete,
  you MUST ask for clarification instead of calling a tool.
- Only call a tool when the selection criteria is explicit.
"""

LEVEL_1_TOOLS = [

    # -------------------------------------------------
    # CREATE ARTIST PLAYLIST
    # -------------------------------------------------
    {
        "type": "function",
        "name": "create_artist_playlist",
        "description": (
            "Create a new playlist containing ALL songs from a specific artist "
            "in the user's local library. "
            "Only call this tool if the artist is explicitly mentioned."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "artist_name": {
                    "type": "string"
                },
                "playlist_name": {
                    "type": "string"
                }
            },
            "required": ["artist_name"]
        }
    },

    # -------------------------------------------------
    # CREATE RECENT PLAYLIST
    # -------------------------------------------------
    {
        "type": "function",
        "name": "create_recent_playlist",
        "description": (
            "Create a new playlist using recently added songs. "
            "Only use this tool if the user explicitly refers to "
            "'recent', 'recently added', or 'last added' songs. "
            "Do NOT assume recency if not clearly stated."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer"
                },
                "playlist_name": {
                    "type": "string"
                }
            }
        }
    },

    # -------------------------------------------------
    # CREATE ALBUM PLAYLIST
    # -------------------------------------------------
    {
        "type": "function",
        "name": "create_album_playlist",
        "description": (
            "Create a new playlist containing ALL songs from a specific album. "
            "Only call this tool if the album name is explicitly mentioned."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "album_name": {
                    "type": "string"
                },
                "playlist_name": {
                    "type": "string"
                }
            },
            "required": ["album_name"]
        }
    },

    # -------------------------------------------------
    # CREATE MIXED PLAYLIST
    # -------------------------------------------------
    {
        "type": "function",
        "name": "create_mixed_playlist",
        "description": (
            "Create a playlist combining explicit selection criteria. "
            "The criteria must be clearly stated by the user. "
            "If the selection logic is incomplete or ambiguous, "
            "ask for clarification instead of calling this tool."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "criteria": {
                    "type": "object",
                    "properties": {
                        "artists": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "artist_limits": {
                            "type": "object",
                            "additionalProperties": {"type": "integer"}
                        },
                        "albums": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "recent_limit": {
                            "type": "integer"
                        },
                        "specific_tracks": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "playlist_name": {
                    "type": "string"
                }
            },
            "required": ["criteria"]
        }
    },

    # -------------------------------------------------
    # RENAME PLAYLIST
    # -------------------------------------------------
    {
        "type": "function",
        "name": "rename_playlist_by_name",
        "description": (
            "Rename an existing playlist identified by its current name."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "playlist_name": {
                    "type": "string"
                },
                "new_name": {
                    "type": "string"
                }
            },
            "required": ["playlist_name", "new_name"]
        }
    },

    # -------------------------------------------------
    # ADD TRACKS TO PLAYLIST (STRICT)
    # -------------------------------------------------
    {
        "type": "function",
        "name": "add_tracks_to_playlist_by_name",
        "description": (
            "Add songs to an existing playlist using explicit selection criteria. "
            "If the user specifies a number of songs for a specific artist, "
            "you MUST use artist_limits. "
            "recent_limit must ONLY be used when the user explicitly refers "
            "to recent or last added songs. "
            "If the selection logic is unclear or incomplete, "
            "ask for clarification instead of calling this tool."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "playlist_name": {
                    "type": "string"
                },
                "criteria": {
                    "type": "object",
                    "properties": {
                        "artists": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "artist_limits": {
                            "type": "object",
                            "additionalProperties": {"type": "integer"}
                        },
                        "albums": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "recent_limit": {
                            "type": "integer"
                        },
                        "specific_tracks": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["playlist_name", "criteria"]
        }
    },

    # -------------------------------------------------
    # REMOVE TRACKS FROM PLAYLIST (STRICT)
    # -------------------------------------------------
    {
        "type": "function",
        "name": "remove_tracks_from_playlist_by_name",
        "description": (
            "Remove songs from an existing playlist using explicit selection criteria. "
            "Do NOT assume defaults. "
            "If the user's selection logic is ambiguous or incomplete, "
            "ask for clarification instead of calling this tool."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "playlist_name": {
                    "type": "string"
                },
                "criteria": {
                    "type": "object",
                    "properties": {
                        "artists": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "artist_limits": {
                            "type": "object",
                            "additionalProperties": {"type": "integer"}
                        },
                        "albums": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "recent_limit": {
                            "type": "integer"
                        },
                        "specific_tracks": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["playlist_name", "criteria"]
        }
    }

]
