from typing import List, Dict, Optional

from langchain.tools import tool
from pydantic import BaseModel, Field

from core.repository import (
    get_tracks_by_artist,
    get_recent_tracks,
    get_tracks_by_album,
)

from core.playlists import (
    create_playlist,
    add_tracks_to_playlist,
    remove_tracks_from_playlist,
    update_playlist_details,
    get_playlist_id_by_name,
)


# Schemas


class RenamePlaylistSchema(BaseModel):
    playlist_name: str = Field(..., min_length=1)
    new_name: str = Field(..., min_length=1)


class CreateArtistPlaylistSchema(BaseModel):
    artist_name: str = Field(..., min_length=1)
    playlist_name: str = Field(..., min_length=1)


class CreateRecentPlaylistSchema(BaseModel):
    limit: int = Field(..., gt=0)
    playlist_name: str = Field(..., min_length=1)


class CreateAlbumPlaylistSchema(BaseModel):
    album_name: str = Field(..., min_length=1)
    playlist_name: str = Field(..., min_length=1)


class MixedCriteriaSchema(BaseModel):
    artists: Optional[List[str]] = None
    artist_limits: Optional[Dict[str, int]] = None
    albums: Optional[List[str]] = None
    recent_limit: Optional[int] = Field(default=None, gt=0)
    specific_tracks: Optional[List[str]] = None


class CreateMixedPlaylistSchema(BaseModel):
    criteria: MixedCriteriaSchema
    playlist_name: str = Field(..., min_length=1)


class ModifyPlaylistSchema(BaseModel):
    playlist_name: str = Field(..., min_length=1)
    criteria: MixedCriteriaSchema


# Tool Builder


def build_level1_tools(conn, sp):

    @tool(args_schema=RenamePlaylistSchema)
    def rename_playlist_by_name(playlist_name: str, new_name: str) -> str:
        """
        Rename an existing playlist identified by its current name.
        Only one tool must be executed per user intention.
        """
        playlist_id = get_playlist_id_by_name(sp, playlist_name)

        if not playlist_id:
            return f"Playlist '{playlist_name}' not found."

        update_playlist_details(sp, playlist_id, name=new_name)

        return f"Playlist '{playlist_name}' renamed to '{new_name}'."

    @tool(args_schema=CreateArtistPlaylistSchema)
    def create_artist_playlist(artist_name: str, playlist_name: str) -> str:
        """
        Create a new playlist using only a single explicit artist criterion.
        Do not use this tool if multiple criteria are present.
        Only one tool must be executed per user intention.
        """
        track_ids = get_tracks_by_artist(conn, artist_name)

        if not track_ids:
            return f"No tracks found for artist '{artist_name}'."

        playlist_id = create_playlist(sp, playlist_name)
        add_tracks_to_playlist(sp, playlist_id, track_ids)

        return f"Playlist '{playlist_name}' created with {len(track_ids)} tracks from '{artist_name}'."

    @tool(args_schema=CreateRecentPlaylistSchema)
    def create_recent_playlist(limit: int, playlist_name: str) -> str:
        """
        Create a new playlist using only a recent tracks limit criterion.
        Do not combine with other filters.
        Only one tool must be executed per user intention.
        """
        track_ids = get_recent_tracks(conn, limit)

        if not track_ids:
            return "No recent tracks found."

        playlist_id = create_playlist(sp, playlist_name)
        add_tracks_to_playlist(sp, playlist_id, track_ids)

        return f"Playlist '{playlist_name}' created with {len(track_ids)} recent tracks."

    @tool(args_schema=CreateAlbumPlaylistSchema)
    def create_album_playlist(album_name: str, playlist_name: str) -> str:
        """
        Create a new playlist using only a single explicit album criterion.
        Do not use this tool if multiple criteria are present.
        Only one tool must be executed per user intention.
        """
        track_ids = get_tracks_by_album(conn, album_name)

        if not track_ids:
            return f"No tracks found for album '{album_name}'."

        playlist_id = create_playlist(sp, playlist_name)
        add_tracks_to_playlist(sp, playlist_id, track_ids)

        return f"Playlist '{playlist_name}' created with {len(track_ids)} tracks from album '{album_name}'."

    @tool(args_schema=CreateMixedPlaylistSchema)
    def create_mixed_playlist(criteria: MixedCriteriaSchema, playlist_name: str) -> str:
        """
        Create a new playlist combining multiple explicit selection criteria.
        Use this tool when more than one filter is provided.
        Only one tool must be executed per user intention.
        """
        track_set = set()

        if criteria.artists:
            for artist in criteria.artists:
                tracks = get_tracks_by_artist(conn, artist)
                if criteria.artist_limits and artist in criteria.artist_limits:
                    tracks = tracks[:criteria.artist_limits[artist]]
                track_set.update(tracks)

        if criteria.albums:
            for album in criteria.albums:
                track_set.update(get_tracks_by_album(conn, album))

        if criteria.recent_limit:
            track_set.update(get_recent_tracks(conn, criteria.recent_limit))

        if criteria.specific_tracks:
            track_set.update(criteria.specific_tracks)

        track_ids = list(track_set)

        if not track_ids:
            return "No tracks matched the given criteria."

        playlist_id = create_playlist(sp, playlist_name)
        add_tracks_to_playlist(sp, playlist_id, track_ids)

        return f"Playlist '{playlist_name}' created with {len(track_ids)} tracks."

    @tool(args_schema=ModifyPlaylistSchema)
    def add_tracks_to_playlist_by_name(playlist_name: str, criteria: MixedCriteriaSchema) -> str:
        """
        Add tracks to a single existing playlist using explicit criteria.
        Treat playlist_name as a literal string.
        Only one tool must be executed per user intention.
        """
        playlist_id = get_playlist_id_by_name(sp, playlist_name)

        if not playlist_id:
            return f"Playlist '{playlist_name}' not found."

        track_set = set()

        if criteria.artists:
            for artist in criteria.artists:
                track_set.update(get_tracks_by_artist(conn, artist))

        if criteria.albums:
            for album in criteria.albums:
                track_set.update(get_tracks_by_album(conn, album))

        if criteria.recent_limit:
            track_set.update(get_recent_tracks(conn, criteria.recent_limit))

        if criteria.specific_tracks:
            track_set.update(criteria.specific_tracks)

        track_ids = list(track_set)

        if not track_ids:
            return "No tracks matched the given criteria."

        add_tracks_to_playlist(sp, playlist_id, track_ids)

        return f"{len(track_ids)} tracks added to playlist '{playlist_name}'."

    @tool(args_schema=ModifyPlaylistSchema)
    def remove_tracks_from_playlist_by_name(playlist_name: str, criteria: MixedCriteriaSchema) -> str:
        """
        Remove tracks from a single existing playlist using explicit criteria.
        Treat playlist_name as a literal string.
        Only one tool must be executed per user intention.
        """
        playlist_id = get_playlist_id_by_name(sp, playlist_name)

        if not playlist_id:
            return f"Playlist '{playlist_name}' not found."

        track_set = set()

        if criteria.artists:
            for artist in criteria.artists:
                track_set.update(get_tracks_by_artist(conn, artist))

        if criteria.albums:
            for album in criteria.albums:
                track_set.update(get_tracks_by_album(conn, album))

        if criteria.recent_limit:
            track_set.update(get_recent_tracks(conn, criteria.recent_limit))

        if criteria.specific_tracks:
            track_set.update(criteria.specific_tracks)

        track_ids = list(track_set)

        if not track_ids:
            return "No tracks matched the given criteria."

        remove_tracks_from_playlist(sp, playlist_id, track_ids)

        return f"{len(track_ids)} tracks removed from playlist '{playlist_name}'."

    return [
        rename_playlist_by_name,
        create_artist_playlist,
        create_recent_playlist,
        create_album_playlist,
        create_mixed_playlist,
        add_tracks_to_playlist_by_name,
        remove_tracks_from_playlist_by_name,
    ]
