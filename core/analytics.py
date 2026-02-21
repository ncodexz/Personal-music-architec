import math


def get_top_tracks_by_recency(conn, limit: int = 10, decay_days: float = 30.0) -> list[tuple[str, float]]:
    """
    Return top tracks ranked by recency-weighted score.
    Uses exponential decay over play_history.
    """

    cursor = conn.cursor()

    cursor.execute(f"""
    SELECT
        ph.track_id,
        SUM(
            ph.weight *
            EXP(
                - (julianday('now') - julianday(ph.played_at)) / {decay_days}
            )
        ) as score
    FROM play_history ph
    GROUP BY ph.track_id
    ORDER BY score DESC
    LIMIT ?;
    """, (limit,))

    return cursor.fetchall()


def get_top_tracks_from_album_by_recency(conn, album_name: str, limit: int = 10, decay_days: float = 30.0) -> list[tuple[str, float]]:
    """
    Return top tracks from specific album ranked by recency decay.
    """

    cursor = conn.cursor()

    cursor.execute(f"""
    SELECT
        ph.track_id,
        SUM(
            ph.weight *
            EXP(
                - (julianday('now') - julianday(ph.played_at)) / {decay_days}
            )
        ) as score
    FROM play_history ph
    JOIN track_albums ta ON ta.track_id = ph.track_id
    JOIN albums a ON a.album_id = ta.album_id
    WHERE a.name = ?
    GROUP BY ph.track_id
    ORDER BY score DESC
    LIMIT ?;
    """, (album_name, limit))

    return cursor.fetchall()


def get_top_artists_by_recency(conn, limit: int = 10, decay_days: float = 30.0) -> list[tuple[str, float]]:
    """
    Return top artists ranked by recency-weighted play score.
    """

    cursor = conn.cursor()

    cursor.execute(f"""
    SELECT
        a.artist_id,
        SUM(
            ph.weight *
            EXP(
                - (julianday('now') - julianday(ph.played_at)) / {decay_days}
            )
        ) as score
    FROM play_history ph
    JOIN track_artists ta ON ta.track_id = ph.track_id
    JOIN artists a ON a.artist_id = ta.artist_id
    GROUP BY a.artist_id
    ORDER BY score DESC
    LIMIT ?;
    """, (limit,))

    return cursor.fetchall()


def get_track_engagement_score(conn, track_id: str) -> float:
    """
    Return engagement score for a specific track from track_metrics.
    """

    cursor = conn.cursor()

    cursor.execute("""
    SELECT engagement_score
    FROM track_metrics
    WHERE track_id = ?;
    """, (track_id,))

    row = cursor.fetchone()

    if row:
        return row[0]

    return 0.0


def rank_tracks_by_engagement(conn, track_ids: list[str]) -> list[tuple[str, float]]:
    """
    Rank given track_ids by engagement_score.
    """

    if not track_ids:
        return []

    cursor = conn.cursor()

    placeholders = ",".join(["?"] * len(track_ids))

    query = f"""
    SELECT track_id, engagement_score
    FROM track_metrics
    WHERE track_id IN ({placeholders})
    ORDER BY engagement_score DESC;
    """

    cursor.execute(query, track_ids)

    return cursor.fetchall()


def get_weighted_score_for_tracks(conn, track_ids: list[str], decay_days: float = 30.0) -> list[tuple[str, float]]:
    """
    Calculate recency-weighted score for a specific subset of track_ids.
    """

    if not track_ids:
        return []

    cursor = conn.cursor()

    placeholders = ",".join(["?"] * len(track_ids))

    query = f"""
    SELECT
        ph.track_id,
        SUM(
            ph.weight *
            EXP(
                - (julianday('now') - julianday(ph.played_at)) / {decay_days}
            )
        ) as score
    FROM play_history ph
    WHERE ph.track_id IN ({placeholders})
    GROUP BY ph.track_id
    ORDER BY score DESC;
    """

    cursor.execute(query, track_ids)

    return cursor.fetchall()