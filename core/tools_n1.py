"""
Level 1 tools.

These functions represent complete human intentions.
They orchestrate:
- Data retrieval from SQLite (repository layer)
- Execution through Spotify (Level 0)

No raw SQL or direct HTTP logic should exist here.
"""

from core.playlists import (
    create_playlist,
    add_tracks_to_playlist,
    remove_tracks_from_playlist,
    update_playlist_details,
    get_current_user_playlists,
)

from core.repository import (
    get_tracks_by_artist,
    get_recent_tracks,
    get_tracks_by_album,
)



# Creation Tools


def create_artist_playlist(conn, sp, artist_name: str, playlist_name: str = None):
    """Create a playlist containing all tracks from a specific artist."""
    track_ids = get_tracks_by_artist(conn, artist_name)

    if not track_ids:
        return {"status": "error", "message": f"No tracks found for artist '{artist_name}'."}

    if not playlist_name:
        playlist_name = f"{artist_name} - Collection"

    playlist_id = create_playlist(sp, playlist_name)
    add_tracks_to_playlist(sp, playlist_id, track_ids)

    return {
        "status": "success",
        "playlist_id": playlist_id,
        "playlist_name": playlist_name,
        "track_count": len(track_ids),
    }


def create_recent_playlist(conn, sp, limit: int = 20, playlist_name: str = None):
    """Create a playlist with the most recently added tracks."""
    track_ids = get_recent_tracks(conn, limit)

    if not track_ids:
        return {"status": "error", "message": "No recent tracks found."}

    if not playlist_name:
        playlist_name = f"Recent {limit} Tracks"

    playlist_id = create_playlist(sp, playlist_name)
    add_tracks_to_playlist(sp, playlist_id, track_ids)

    return {
        "status": "success",
        "playlist_id": playlist_id,
        "playlist_name": playlist_name,
        "track_count": len(track_ids),
    }


def create_album_playlist(conn, sp, album_name: str, playlist_name: str = None):
    """Create a playlist containing all tracks from a specific album."""
    track_ids = get_tracks_by_album(conn, album_name)

    if not track_ids:
        return {"status": "error", "message": f"No tracks found for album '{album_name}'."}

    if not playlist_name:
        playlist_name = f"{album_name} - Album Collection"

    playlist_id = create_playlist(sp, playlist_name)
    add_tracks_to_playlist(sp, playlist_id, track_ids)

    return {
        "status": "success",
        "playlist_id": playlist_id,
        "playlist_name": playlist_name,
        "track_count": len(track_ids),
    }


def create_mixed_playlist(conn, sp, criteria: dict, playlist_name: str = None):
    """
    Create a playlist combining multiple criteria.

    Supported criteria keys:
    - artists: list[str]
    - artist_limits: dict[str, int]
    - albums: list[str]
    - recent_limit: int (only applied if explicitly provided)
    - specific_tracks: list[str]
    """
    track_set = set()

    # Artist-based selection
    artists = criteria.get("artists", [])
    artist_limits = criteria.get("artist_limits", {})

    for artist in artists:
        tracks = get_tracks_by_artist(conn, artist)
        if artist in artist_limits:
            tracks = tracks[:artist_limits[artist]]
        track_set.update(tracks)

    # Album-based selection
    for album in criteria.get("albums", []):
        track_set.update(get_tracks_by_album(conn, album))

    # Recent selection (only if provided)
    if "recent_limit" in criteria:
        recent_limit = criteria.get("recent_limit") or 20
        track_set.update(get_recent_tracks(conn, recent_limit))

    # Specific track IDs
    track_set.update(criteria.get("specific_tracks", []))

    track_ids = list(track_set)

    if not track_ids:
        return {"status": "error", "message": "No tracks matched the given criteria."}

    if not playlist_name:
        playlist_name = "Mixed Playlist"

    playlist_id = create_playlist(sp, playlist_name)
    add_tracks_to_playlist(sp, playlist_id, track_ids)

    return {
        "status": "success",
        "playlist_id": playlist_id,
        "playlist_name": playlist_name,
        "track_count": len(track_ids),
    }



# Modification Tools


def rename_playlist_by_name(sp, playlist_name: str, new_name: str):
    """Rename an existing playlist identified by its name."""
    playlists = get_current_user_playlists(sp)

    for item in playlists["items"]:
        if item["name"].lower() == playlist_name.lower():
            update_playlist_details(sp, item["id"], name=new_name)
            return {
                "status": "success",
                "playlist_id": item["id"],
                "old_name": playlist_name,
                "new_name": new_name,
            }

    return {"status": "error", "message": f"Playlist '{playlist_name}' not found."}


def add_tracks_to_playlist_by_name(conn, sp, playlist_name: str, criteria: dict):
    """Add tracks to an existing playlist based on selection criteria."""
    playlists = get_current_user_playlists(sp)

    playlist_id = None
    for item in playlists["items"]:
        if item["name"].lower() == playlist_name.lower():
            playlist_id = item["id"]
            break

    if not playlist_id:
        return {"status": "error", "message": f"Playlist '{playlist_name}' not found."}

    track_set = set()

    for artist in criteria.get("artists", []):
        track_set.update(get_tracks_by_artist(conn, artist))

    for album in criteria.get("albums", []):
        track_set.update(get_tracks_by_album(conn, album))

    if "recent_limit" in criteria:
        recent_limit = criteria.get("recent_limit") or 20
        track_set.update(get_recent_tracks(conn, recent_limit))

    track_set.update(criteria.get("specific_tracks", []))

    track_ids = list(track_set)

    if not track_ids:
        return {"status": "error", "message": "No tracks matched the given criteria."}

    add_tracks_to_playlist(sp, playlist_id, track_ids)

    return {"status": "success", "playlist_id": playlist_id, "added_count": len(track_ids)}


def remove_tracks_from_playlist_by_name(conn, sp, playlist_name: str, criteria: dict):
    """Remove tracks from an existing playlist based on selection criteria."""
    playlists = get_current_user_playlists(sp)

    playlist_id = None
    for item in playlists["items"]:
        if item["name"].lower() == playlist_name.lower():
            playlist_id = item["id"]
            break

    if not playlist_id:
        return {"status": "error", "message": f"Playlist '{playlist_name}' not found."}

    track_set = set()

    for artist in criteria.get("artists", []):
        track_set.update(get_tracks_by_artist(conn, artist))

    for album in criteria.get("albums", []):
        track_set.update(get_tracks_by_album(conn, album))

    if "recent_limit" in criteria:
        recent_limit = criteria.get("recent_limit") or 20
        track_set.update(get_recent_tracks(conn, recent_limit))

    track_set.update(criteria.get("specific_tracks", []))

    track_ids = list(track_set)

    if not track_ids:
        return {"status": "error", "message": "No tracks matched the given criteria."}

    remove_tracks_from_playlist(sp, playlist_id, track_ids)

    return {"status": "success", "playlist_id": playlist_id, "removed_count": len(track_ids)}
