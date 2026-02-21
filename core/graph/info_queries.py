from typing import Tuple, Optional
from core.graph.state import MusicState


def info_query_node(state: MusicState, conn) -> MusicState:
    """
    Handle informational queries deterministically.
    """

    user_input = state["user_input"].lower()

    cursor = conn.cursor()

    # --- Artist existence / count ---
    if "canción" in user_input or "song" in user_input:
        # Try to extract artist name heuristically
        words = user_input.split()
        artist_name = words[-1].replace("?", "").replace("¿", "")

        cursor.execute("""
        SELECT COUNT(*)
        FROM tracks t
        JOIN track_artists ta ON t.track_id = ta.track_id
        JOIN artists a ON ta.artist_id = a.artist_id
        WHERE LOWER(a.name) = LOWER(?)
        """, (artist_name,))

        count = cursor.fetchone()[0]

        if count > 0:
            state["clarification_message"] = f"Yes, you have {count} tracks by {artist_name.title()}."
        else:
            state["clarification_message"] = f"No, you do not have any tracks by {artist_name.title()}."

        return state

    # --- Most played track ---
    if "most played" in user_input or "más escuchada" in user_input:
        cursor.execute("""
        SELECT ph.track_id, COUNT(*) as play_count
        FROM play_history ph
        GROUP BY ph.track_id
        ORDER BY play_count DESC
        LIMIT 1
        """)

        row = cursor.fetchone()

        if not row:
            state["clarification_message"] = "You do not have enough listening data yet."
            return state

        track_id = row[0]

        cursor.execute("""
        SELECT name
        FROM tracks
        WHERE track_id = ?
        """, (track_id,))

        track_name = cursor.fetchone()[0]

        state["clarification_message"] = f"Your most played track is '{track_name}'."

        return state

    # --- Recent listening ---
    if "recent" in user_input or "recientemente" in user_input:
        cursor.execute("""
        SELECT t.name
        FROM play_history ph
        JOIN tracks t ON ph.track_id = t.track_id
        ORDER BY ph.played_at DESC
        LIMIT 5
        """)

        rows = cursor.fetchall()

        if not rows:
            state["clarification_message"] = "You have not listened to anything recently."
            return state

        track_list = ", ".join([r[0] for r in rows])

        state["clarification_message"] = f"Recently you listened to: {track_list}."

        return state

    # --- Fallback ---
    state["clarification_message"] = "I am not able to answer that informational request yet."

    return state