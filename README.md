Personal Music Architect
Playlist Module – Operational Documentation
1. Architectural Context
The Playlist module belongs to Phase 1 (Structural Layer) of the project.
This phase does not include:
AI
Embeddings
RAG
Semantic reasoning
Agent orchestration logic
This phase provides:
Persistent SQLite storage
Incremental synchronization from Spotify
Atomic playlist manipulation tools
Clean separation between persistence, ingestion, and actions
The playlist module contains atomic tools only.
No complex logic.
No interpretation.
No emotional reasoning.
All orchestration will live in the future Agent layer.
2. Required Initialization Before Using Playlist Functions
Before calling any playlist function, the following must be initialized in the notebook:
2.1 Project Root
The notebook must run from the project root:
import os
import sys

PROJECT_ROOT = os.path.abspath("..")
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
2.2 Spotify Authentication
import spotipy
from spotipy.oauth2 import SpotifyOAuth

SCOPE = (
    "playlist-read-private "
    "playlist-modify-public "
    "playlist-modify-private "
    "user-library-read"
)

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        scope=SCOPE,
        cache_path=".spotify_cache"
    )
)
Important:
Token must include playlist modification scopes.
Cache file is stored in project root.
If cache is deleted, authentication flow will restart.
2.3 Database Initialization
from core.database import get_connection, create_tables

conn = get_connection("music_agent.db")
create_tables(conn)
If this is a fresh setup, you must also sync:
from core.ingestion import sync_new_tracks
from core.database import get_latest_added_at

sync_new_tracks(sp, conn, get_latest_added_at)
3. Playlist Module Overview
File:
core/playlists.py
The module provides:
Local database track retrieval
Playlist creation
Playlist update
Playlist item addition
Playlist item removal
Playlist replacement
Playlist deletion
Playlist item retrieval
All tools are atomic and deterministic.
4. Database Query Tool
get_tracks(conn, artist=None, order_by="added_at DESC", limit=None)
Purpose:
Retrieve tracks from local SQLite database.
Example:
tracks = get_tracks(conn, artist="Eminem")
Returns:
[
    (track_id, name, added_at),
    ...
]
Notes:
Filtering is case-insensitive.
Sorting is SQL-based.
Does not call Spotify API.
Operates only on local DB.
5. Playlist Creation
create_playlist(sp, name, public=False)
Creates a new playlist.
Example:
playlist_id = create_playlist(sp, "Eminem - 17", public=True)
Returns:
playlist_id (string)
Uses endpoint:
POST /me/playlists
Confirmed working.
6. Add Tracks to Playlist
add_tracks_to_playlist(sp, playlist_id, track_ids)
Adds tracks in batches of 100.
Example:
add_tracks_to_playlist(sp, playlist_id, track_ids)
Important:
Uses /items endpoint.
Automatically chunks in groups of 100.
Expects raw track IDs (not URIs).
Working implementation verified.
7. Remove Tracks from Playlist
Spotipy 2.25.2 has a DELETE body issue.
Problem
Spotipy sends DELETE payload using data= instead of proper JSON formatting.
Spotify returns:
400 Bad Request
No uris provided
Solution
Manual request using requests.
remove_tracks_from_playlist(sp, playlist_id, track_ids)
Example:
remove_tracks_from_playlist(sp, playlist_id, [track_id])
Implementation:
Retrieves OAuth token
Sends DELETE to /items
Uses json=payload
Validates status code
Confirmed working.
8. Replace Playlist Tracks
replace_playlist_tracks(sp, playlist_id, track_ids)
Replaces entire playlist content.
Example:
replace_playlist_tracks(sp, playlist_id, new_track_ids)
Uses:
PUT /playlists/{playlist_id}/items
Confirmed functional.
9. Update Playlist Details
update_playlist_details(sp, playlist_id, name=None, public=None)
Example:
update_playlist_details(sp, playlist_id, name="Eminem - 16")
Uses:
PUT /playlists/{playlist_id}
Confirmed working.
10. Unfollow / Delete Playlist
unfollow_playlist(sp, playlist_id)
Example:
unfollow_playlist(sp, playlist_id)
Uses:
DELETE /playlists/{playlist_id}/followers
Confirmed functional.
11. Get Playlist Metadata
Using:
playlist_data = sp.playlist(playlist_id)
Important structural note:
In Spotipy 2.25.2:
playlist_data["items"]["total"]
NOT:
playlist_data["tracks"]["total"]
The tracks field is deprecated.
Always inspect real response structure.
12. Get Playlist Items
Spotipy's playlist_items() internally calls deprecated /tracks.
To ensure compatibility with Spotify API v1:
Manual implementation using /items endpoint is recommended.
Confirmed working implementation uses:
GET /playlists/{playlist_id}/items
via requests.
Returned structure:
{
  "items": [
      {
          "item": { ... track object ... }
      }
  ],
  "total": integer
}
Track name access:
item["item"]["name"]
13. Confirmed Working Operations
Verified end-to-end:
Initial DB sync
Track filtering
Playlist creation
Batch add
Remove single track
Remove multiple tracks
Rename playlist
Replace content
Unfollow playlist
Retrieve playlist metadata
Retrieve playlist items
All validated in clean notebook environment.
14. Known Limitations
Spotipy 2.25.2 DELETE implementation issue.
Deprecated /tracks endpoint used internally by Spotipy.
Manual HTTP requests required for strict compliance with /items.
15. Design Philosophy Maintained
Notebook = laboratory
core/ = production layer
Tools are atomic
No semantic logic inside tools
SQLite = source of truth
Spotify = ingestion source
No over-engineering
Clean separation of layers
Agent layer not yet implemented
16. Phase Status
Playlist module: Stable
Database layer: Stable
Ingestion layer: Stable
Phase 1 (Structural Layer): Functionally complete and validated.
If you want, next step we can:
Add a structured "Initialization Block Template" section for all future notebooks
Or draft the closing section of Phase 1 formally and prepare transition to Phase 2