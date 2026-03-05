# Personal Music Architect

Personal Music Architect is an intelligent music management agent that connects to your Spotify library and allows you to create, modify, and analyze playlists using natural language.

The system combines deterministic playlist building with semantic retrieval using vector embeddings to generate playlists based on artists, listening behavior, and emotional context.

---

## Overview

The agent interacts with your personal Spotify library and supports requests such as:

* Creating playlists from specific artists or albums
* Generating playlists based on moods or emotions
* Modifying existing playlists
* Querying information about your music library

Example commands:

```
Create a playlist with songs by Drake
Create a sad playlist
Create a nostalgic playlist
How many songs do I have in my library?
List my playlists
Add more songs to my playlist
Delete playlist AI Generated Playlist
```

---

## Architecture

The system is composed of several layers:

```
User Input
     ↓
Session Manager
     ↓
LangGraph Agent
     ↓
Strategy → Validation → Composition → Execution
     ↓
Spotify API + Semantic Engine
```

Core components:

* **Session Layer**
  Handles conversation context and session memory.

* **Graph Agent (LangGraph)**
  Executes the workflow for interpreting and fulfilling user requests.

* **Deterministic Composition Engine**
  Builds playlists based on explicit sources such as artists, albums, or listening history.

* **Semantic Engine (RAG)**
  Uses embeddings and vector search to find musically related tracks.

* **Spotify Integration**
  Executes playlist creation and modification via the Spotify API.

---

## Semantic Recommendation Engine

The system supports hybrid semantic retrieval.

### Emotional Anchors

Anchors represent curated emotional concepts created from playlists.

Example:

```
ANCHOR_SAD
ANCHOR_HIGH CHILL
ANCHOR_POWERFULL
```

Each anchor is converted into a centroid vector in Pinecone.

When a user asks for:

```
Create a sad playlist
```

the system retrieves tracks similar to the anchor vector.

---

### Semantic Fallback

If a requested emotion does not have a predefined anchor, the system performs direct semantic search.

Example:

```
Create a nostalgic playlist
```

Pipeline:

```
emotion text
      ↓
text embedding
      ↓
vector similarity search
      ↓
tracks from your library
```

This allows the system to generate playlists for **any mood or concept**.

---

## Technology Stack

* Python
* SQLite
* LangGraph
* OpenAI Embeddings
* Pinecone Vector Database
* Spotify Web API (Spotipy)
* LangChain

---

## Project Structure

```
.
├── core
│   ├── graph
│   ├── semantic
│   ├── ingestion.py
│   ├── playlists.py
│   ├── repository.py
│   └── database.py
│
├── session
│   ├── manager.py
│   └── context.py
│
├── notebooks
│   └── testing notebooks
│
├── main.py
├── music_agent.db
└── README.md
```

---

## Installation

Clone the repository:

```
git clone <repository-url>
cd personal-music-architect
```

Create a virtual environment:

```
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file:

```
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
```

---

## Running the Agent

Start the system with:

```
python main.py
```

You will see:

```
System ready.
Type 'exit' to quit.
```

Then interact with the agent directly.

---

## Example Usage

Create a playlist from an artist:

```
Create a playlist with songs by Drake
```

Create a mood-based playlist:

```
Create a sad playlist
```

Create a playlist from a new emotion:

```
Create a nostalgic playlist
```

Query library information:

```
How many songs do I have in my library?
```

---

## Future Improvements

Potential extensions for the system:

* automatic anchor generation
* behavioral recommendation integration
* playlist evolution based on listening patterns
* anchor discovery through clustering
* improved conversational reasoning

---

## License

MIT License
