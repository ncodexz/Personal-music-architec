from datetime import datetime
import uuid


def convert_playlist_to_anchor(repo, playlist_id: str, playlist_name: str):
    """
    Converts a playlist with prefix ANCHOR_ into a semantic anchor.

    Steps:
    1. Validate prefix
    2. Extract anchor name
    3. Retrieve playlist tracks
    4. Replace existing anchor if present
    5. Create new anchor
    6. Associate tracks with anchor
    """

    if not playlist_name.startswith("ANCHOR_"):
        return None

    anchor_name = playlist_name.replace("ANCHOR_", "").strip().lower()

    if not anchor_name:
        return None

    track_ids = repo.get_playlist_tracks(playlist_id)

    if not track_ids:
        return None

    # Remove existing anchor with the same name
    existing = repo.get_anchor_by_name(anchor_name)
    if existing:
        repo.delete_anchor(existing["anchor_id"])

    # Create new anchor
    anchor_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    repo.create_anchor(
        anchor_id=anchor_id,
        name=anchor_name,
        created_at=now,
        updated_at=now
    )

    # Associate tracks with anchor
    for track_id in track_ids:
        repo.add_track_to_anchor(anchor_id, track_id)

    return anchor_id