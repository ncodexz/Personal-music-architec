from typing import List, Tuple


def find_similar_tracks_behavioral(conn, track_id: str, limit: int = 5) -> List[str]:
    """
    Behavioral similarity based on:

    1. Co-occurrence in listening sessions (time proximity)
    2. Shared artists
    3. Engagement score proximity

    Returns ordered list of similar track_ids.
    """

    co_occurrence_scores = _co_occurrence_score(conn, track_id)
    artist_overlap_scores = _artist_overlap_score(conn, track_id)
    engagement_scores = _engagement_proximity_score(conn, track_id)

    combined_scores = {}

    for tid, score in co_occurrence_scores:
        combined_scores[tid] = combined_scores.get(tid, 0) + score * 3

    for tid, score in artist_overlap_scores:
        combined_scores[tid] = combined_scores.get(tid, 0) + score * 2

    for tid, score in engagement_scores:
        combined_scores[tid] = combined_scores.get(tid, 0) + score * 1

    if track_id in combined_scores:
        del combined_scores[track_id]

    ranked = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

    return [tid for tid, _ in ranked[:limit]]


# -------------------------
# INTERNAL SCORING METHODS
# -------------------------

def _co_occurrence_score(conn, track_id: str) -> List[Tuple[str, float]]:
    """
    Tracks played within 1 hour window of target track.
    """

    cursor = conn.cursor()

    cursor.execute("""
        SELECT ph2.track_id, COUNT(*) as score
        FROM play_history ph1
        JOIN play_history ph2
            ON ABS(strftime('%s', ph1.played_at) - strftime('%s', ph2.played_at)) <= 3600
        WHERE ph1.track_id = ?
          AND ph2.track_id != ?
        GROUP BY ph2.track_id
        ORDER BY score DESC
    """, (track_id, track_id))

    return cursor.fetchall()


def _artist_overlap_score(conn, track_id: str) -> List[Tuple[str, float]]:
    """
    Tracks sharing same artist.
    """

    cursor = conn.cursor()

    cursor.execute("""
        SELECT ta2.track_id, COUNT(*) as score
        FROM track_artists ta1
        JOIN track_artists ta2
            ON ta1.artist_id = ta2.artist_id
        WHERE ta1.track_id = ?
          AND ta2.track_id != ?
        GROUP BY ta2.track_id
        ORDER BY score DESC
    """, (track_id, track_id))

    return cursor.fetchall()


def _engagement_proximity_score(conn, track_id: str) -> List[Tuple[str, float]]:
    """
    Tracks with similar engagement score.
    """

    cursor = conn.cursor()

    cursor.execute("""
        SELECT engagement_score
        FROM track_metrics
        WHERE track_id = ?
    """, (track_id,))

    row = cursor.fetchone()

    if not row:
        return []

    target_score = row[0]

    cursor.execute("""
        SELECT track_id,
               1.0 / (1.0 + ABS(engagement_score - ?)) as score
        FROM track_metrics
        WHERE track_id != ?
        ORDER BY score DESC
        LIMIT 50
    """, (target_score, track_id))

    return cursor.fetchall()