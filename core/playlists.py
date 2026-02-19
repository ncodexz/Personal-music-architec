import requests


# Playlist Discovery


def get_current_user_playlists(sp, limit=50, offset=0):
    """
    Retrieve playlists owned or followed by the current user.
    """
    return sp.current_user_playlists(limit=limit, offset=offset)


def get_playlist_id_by_name(sp, playlist_name: str):
    """
    Retrieve playlist ID by playlist name.
    Returns None if not found.
    """
    playlists = sp.current_user_playlists(limit=50)

    for item in playlists["items"]:
        if item["name"].lower() == playlist_name.lower():
            return item["id"]

    return None


def get_latest_playlist(sp):
    """
    Retrieve the most recently created playlist.
    Assumes playlists are returned in descending order.
    """
    playlists = sp.current_user_playlists(limit=1)

    items = playlists.get("items", [])
    if not items:
        return None

    return items[0]


# Playlist Creation


def create_playlist(sp, name: str, public: bool = False):
    """
    Create a new playlist and return its ID.
    Uses official /me/playlists endpoint.
    """
    playlist = sp._post(
        "me/playlists",
        payload={
            "name": name,
            "public": public
        }
    )

    return playlist["id"]


# Playlist Modification


def update_playlist_details(sp, playlist_id: str, name=None, public=None):
    """
    Update playlist details such as name or public state.
    """
    payload = {}

    if name is not None:
        payload["name"] = name

    if public is not None:
        payload["public"] = public

    if payload:
        sp.playlist_change_details(playlist_id, **payload)


def add_tracks_to_playlist(sp, playlist_id: str, track_ids: list):
    """
    Add track IDs to a playlist using official /items endpoint.
    """
    track_uris = [f"spotify:track:{tid}" for tid in track_ids]

    for i in range(0, len(track_uris), 100):
        sp._post(
            f"playlists/{playlist_id}/items",
            payload={
                "uris": track_uris[i:i+100]
            }
        )


def remove_tracks_from_playlist(sp, playlist_id, track_ids):
    """
    Remove track IDs from a playlist.
    """
    token = sp.auth_manager.get_access_token(as_dict=False)

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/items"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "items": [
            {"uri": f"spotify:track:{tid}"} for tid in track_ids
        ]
    }

    response = requests.delete(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to remove tracks. Status: {response.status_code}, Response: {response.text}"
        )

    return response.json()


def replace_playlist_tracks(sp, playlist_id: str, track_ids: list):
    """
    Replace all tracks in a playlist.
    """
    track_uris = [f"spotify:track:{tid}" for tid in track_ids]

    sp.playlist_replace_items(
        playlist_id,
        track_uris
    )


# Playlist Retrieval


def get_playlist(sp, playlist_id: str):
    """
    Retrieve full playlist details.
    """
    return sp.playlist(playlist_id)


def get_playlist_items(sp, playlist_id: str, limit=100, offset=0):
    """
    Retrieve playlist items.
    """
    return sp.playlist_items(
        playlist_id,
        limit=limit,
        offset=offset
    )
