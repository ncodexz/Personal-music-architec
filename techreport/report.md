Technical Report
Spotipy DELETE Request Issue – Playlist Item Removal
1. Summary
While developing the Personal Music Architect project, an issue was identified with the DELETE operation for removing items from a playlist using Spotipy version 2.25.2.
The failure occurs when calling:
sp._delete(f"playlists/{playlist_id}/items", payload=payload)
The request results in:
HTTP 400 - No uris provided
Despite the payload being correctly constructed according to Spotify’s official Web API documentation.
2. Affected Environment
Python: 3.13
Spotipy: 2.25.2
Spotify Web API endpoint:
DELETE /v1/playlists/{playlist_id}/items
Authentication: OAuth (valid scopes confirmed)
3. Expected Behavior
According to Spotify's official documentation:
Endpoint:
DELETE /playlists/{playlist_id}/items
Expected JSON body:
{
  "items": [
    { "uri": "spotify:track:TRACK_ID" }
  ]
}
When correctly formatted, Spotify should return:
200 OK
{
  "snapshot_id": "..."
}
4. Observed Failure
When using Spotipy’s internal _delete() method:
def remove_tracks_from_playlist(sp, playlist_id, track_ids):
    track_uris = [{"uri": f"spotify:track:{tid}"} for tid in track_ids]

    sp._delete(
        f"playlists/{playlist_id}/items",
        payload={
            "tracks": track_uris
        }
    )
The API returns:
400 Bad Request
No uris provided
Even when using the correct "items" key instead of "tracks".
5. Root Cause Analysis
Inspection of Spotipy’s internal implementation:
def _delete(self, url, args=None, payload=None, **kwargs):
    return self._internal_call("DELETE", url, payload, kwargs)
And inside _internal_call:
if payload:
    args["data"] = json.dumps(payload)
Spotipy sends the request body using:
data=json.dumps(payload)
However, Spotify’s Web API expects JSON in the request body with proper Content-Type: application/json and correct JSON handling.
When using requests.delete(..., json=payload) instead of data=, the request works correctly.
This indicates that Spotipy’s _delete() implementation does not correctly format the request body in a way accepted by Spotify for this endpoint.
6. Working Solution (Manual Override)
To resolve the issue, the DELETE request was implemented manually using requests:
import requests

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
Result:
200 OK
{
  "snapshot_id": "..."
}
Confirmed functional.
7. Additional Observation
Spotipy’s playlist_items() method internally calls:
/playlists/{playlist_id}/tracks
Which is marked as deprecated in Spotify’s official documentation.
This may explain additional inconsistencies and 403 responses observed during development.
8. Impact
DELETE playlist item operations fail when using Spotipy’s internal _delete() method.
Requires manual requests workaround to comply with Spotify’s API behavior.
Introduces architectural inconsistency when mixing Spotipy and direct HTTP calls.
9. Recommendation
Spotipy should:
Update _delete() implementation to use json=payload instead of data=json.dumps(payload) where appropriate.
Ensure playlist-related endpoints use /items instead of deprecated /tracks.
Align fully with Spotify Web API v1 current documentation.
10. Status
Workaround implemented successfully.
System operational using manual DELETE request.
Issue reproducible in Spotipy 2.25.2.