import requests


def get_tracks(conn, artist=None, order_by="added_at DESC", limit=None):
    cursor = conn.cursor()

    query = """
    SELECT t.track_id, t.name, t.added_at
    FROM tracks t
    JOIN track_artists ta ON t.track_id = ta.track_id
    JOIN artists a ON ta.artist_id = a.artist_id
    """

    conditions = []
    params = []

    if artist:
        conditions.append("LOWER(a.name) = LOWER(?)")
        params.append(artist)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += f" ORDER BY t.{order_by}"

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    cursor.execute(query, params)
    return cursor.fetchall()


def create_playlist(sp, name, public=False):
    playlist = sp._post("me/playlists", payload={
        "name": name,
        "public": public
    })
    return playlist["id"]


def add_tracks_to_playlist(sp, playlist_id, track_ids):
    track_uris = [f"spotify:track:{tid}" for tid in track_ids]

    for i in range(0, len(track_uris), 100):
        sp._post(
            f"playlists/{playlist_id}/items",
            payload={
                "uris": track_uris[i:i+100]
            }
        )


def remove_tracks_from_playlist(sp, playlist_id, track_ids):
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


def replace_playlist_tracks(sp, playlist_id, track_ids):
    track_uris = [f"spotify:track:{tid}" for tid in track_ids]

    sp._put(
        f"playlists/{playlist_id}/items",
        payload={
            "uris": track_uris
        }
    )


def update_playlist_details(sp, playlist_id, name=None, public=None):
    payload = {}

    if name is not None:
        payload["name"] = name

    if public is not None:
        payload["public"] = public

    sp._put(f"playlists/{playlist_id}", payload=payload)


def unfollow_playlist(sp, playlist_id):
    sp.current_user_unfollow_playlist(playlist_id)


def get_playlist(sp, playlist_id):
    """
    Retrieve full details of a playlist.
    """
    return sp.playlist(playlist_id)


def get_playlist_items(sp, playlist_id, limit=100, offset=0):
    """
    Retrieve items from a playlist.
    """
    return sp.playlist_items(
        playlist_id,
        limit=limit,
        offset=offset
    )


def get_current_user_playlists(sp, limit=50, offset=0):
    """
    Retrieve playlists owned or followed by the current user.
    """
    return sp.current_user_playlists(
        limit=limit,
        offset=offset
    )



def get_playlist_items(sp, playlist_id, limit=100, offset=0):
    """
    Retrieve playlist items using the official /items endpoint.
    Avoids deprecated /tracks endpoint used internally by older Spotipy versions.
    """
    token = sp.auth_manager.get_access_token(as_dict=False)

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/items"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
        "limit": limit,
        "offset": offset
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to retrieve playlist items. Status: {response.status_code}, Response: {response.text}"
        )

    return response.json()
