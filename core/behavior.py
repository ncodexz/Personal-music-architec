# core/behavior.py

from datetime import datetime


def ingest_recently_played(sp, repo, limit: int = 50) -> int:
    results = sp.current_user_recently_played(limit=limit)

    inserted = 0

    for item in results.get("items", []):
        track = item.get("track")
        if not track:
            continue

        track_id = track.get("id")
        played_at = item.get("played_at")

        if not track_id or not played_at:
            continue

        if not repo.track_exists(track_id):
            continue

        context = item.get("context")
        context_type = None
        context_id = None

        if context:
            context_type = context.get("type")
            context_uri = context.get("uri")

            if context_uri and ":" in context_uri:
                context_id = context_uri.split(":")[-1]

        repo.insert_play_event(
            track_id=track_id,
            played_at=played_at,
            context_type=context_type,
            context_id=context_id,
            source="spotify_recent",
            weight=1.0
        )

        inserted += 1

    return inserted


def simulate_play_event(repo, track_id: str, played_at: str | None = None, weight: float = 1.0):

    if not played_at:
        played_at = datetime.utcnow().isoformat()

    if not repo.track_exists(track_id):
        return

    repo.insert_play_event(
        track_id=track_id,
        played_at=played_at,
        context_type=None,
        context_id=None,
        source="simulated",
        weight=weight
    )


def simulate_bulk_behavior(repo, track_ids: list[str], plays_per_track: int = 5) -> int:

    inserted = 0

    for track_id in track_ids:
        for _ in range(plays_per_track):
            simulate_play_event(repo, track_id)
            inserted += 1

    return inserted