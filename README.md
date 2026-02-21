. Overview
Personal Music Architect is a modular music intelligence system designed to operate over a user's Spotify ecosystem.
This is not a simple playlist bot.
It is being built as a scalable, production-grade architecture intended to evolve into a multimodal intelligent music architect capable of:
Structuring a personal music ecosystem.
Designing optimized playlists.
Analyzing engagement patterns.
Operating under controlled autonomy.
This document reflects the state of the project after closing Level 1 — Deterministic Execution Layer.
2. Architectural Philosophy
The project follows strict engineering principles:
Infrastructure first.
Clear separation of responsibilities.
SQLite as the single source of truth.
Spotify as execution layer only.
LLM decides structure, backend executes.
No premature complexity.
Phased evolution.
Deterministic layer separated from creative layer.
No mixing execution and cognition.
Level 1 is intentionally deterministic.
It does not reason.
It executes explicit, structured intentions.
3. Current Architecture
Level 0 — Infrastructure (Closed)
Responsible for:
Spotify API execution.
SQLite persistence.
Data ingestion and synchronization.
Modules:
database.py → SQLite connection and table creation.
repository.py → Pure SQL data access layer.
playlists.py → Spotify execution layer.
ingestion.py → Sync saved tracks into SQLite.
SQLite schema includes:
tracks
artists
albums
track_artists
track_albums
Spotify communication uses:
Spotipy where stable.
Direct API endpoints when necessary (e.g. /items instead of deprecated /tracks).
Level 1 — Deterministic Executor (Closed)
Responsible for:
Executing structured user intentions.
Enforcing single structural action per request.
Validating input using Pydantic schemas.
Preventing ambiguous multi-tool execution.
Stack:
LangChain
ChatOpenAI
@tool decorator
Pydantic validation
Deterministic guard logic
4. Deterministic Design Rules
Level 1 enforces:
One user intention = one structural action.
No chained tool execution.
No implicit defaults.
No interpretation of ambiguous requests.
No cognitive reasoning.
No multi-step orchestration.
If a request contains multiple structural actions:
The system returns:
Ambiguous request. Multiple structural actions detected.
Please specify a single clear intention.
This is intentional.
Creative reasoning belongs to a future layer.
5. Implemented Tools (Level 1)
All tools use strict Pydantic schemas.
Creation
create_artist_playlist
create_recent_playlist
create_album_playlist
create_mixed_playlist
Modification
rename_playlist_by_name
add_tracks_to_playlist_by_name
remove_tracks_from_playlist_by_name
All tools:
Query via repository.py
Execute via playlists.py
Contain no raw SQL
Contain no direct HTTP logic
Do not mix responsibilities
6. Execution Flow
User Request
↓
LangChain Agent
↓
Schema Validation (Pydantic)
↓
Single Tool Selection
↓
Repository (data selection)
↓
Playlist Layer (Spotify execution)
↓
Structured Response
No tool chaining is allowed.
7. Testing Status
The following have been validated:
Playlist creation by artist
Playlist creation by album
Playlist creation by recency
Mixed playlist creation
Track addition
Track removal
Playlist rename
Multi-intention blocking
SQLite thread safety
Spotify endpoint compatibility
Level 1 is stable and production-ready within its deterministic scope.
8. What This Layer Does NOT Do
Level 1 does not:
Perform reasoning.
Detect ambiguities.
Propose optimizations.
Analyze engagement.
Use embeddings.
Use RAG.
Perform similarity search.
Execute multiple actions per request.
Those belong to the next phase.
9. Next Phase (Planned)
Level 2 — Creative / Strategic Agent
Will introduce:
Intent interpretation.
Context retrieval (RAG).
Library analysis.
Playlist optimization logic.
Multi-step planning.
Confirmation before structural changes.
This layer will operate above the deterministic executor.
10. Project Status
Level 0: Closed
Level 1: Closed
Deterministic guard: Active
Architecture: Stable
Ready for Creative Layer design