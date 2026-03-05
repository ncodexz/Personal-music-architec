import os
import sys
from dotenv import load_dotenv

from core.database import create_tables
from core.db_session import DatabaseSession
from core.repository import Repository
from core.graph.builder import build_music_graph
from core.semantic.embeddings import EmbeddingService
from session.manager import SessionManager
from core.semantic.pinecone_indexer import PineconeIndexer
from core.semantic.semantic_service import SemanticService

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from langchain_openai import ChatOpenAI


class AppContainer:
    def __init__(self):
        self.project_root = None
        self.db_session = None
        self.repo = None
        self.sp = None
        self.llm = None
        self.embedding_service = None
        self.graph = None
        self.session = None
        self.pinecone_indexer = None
        self.semantic_service = None

def init_system():
    container = AppContainer()

    # 1. Resolve project root
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
    container.project_root = project_root

    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # 2. Load environment variables
    load_dotenv(os.path.join(project_root, ".env"))

    # 3. Initialize database
    db_path = os.path.join(project_root, "music_agent.db")

    db_session = DatabaseSession(db_path)
    create_tables(db_session.conn)

    container.db_session = db_session
    container.repo = Repository(db_session)

    # 4. Initialize Spotify client
    sp = Spotify(
        auth_manager=SpotifyOAuth(
            scope=(
                "playlist-modify-private "
                "playlist-modify-public "
                "playlist-read-private "
                "user-read-recently-played"
            )
        )
    )
    container.sp = sp

    # 5. Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )
    container.llm = llm

    # 6. Initialize Embedding service
    embedding_service = EmbeddingService(
        api_key=os.getenv("OPENAI_API_KEY")
    )
    container.embedding_service = embedding_service

    # 7. Initialize Pinecone indexer
    pinecone_indexer = PineconeIndexer(
        api_key=os.getenv("PINECONE_API_KEY"),
        index_name="personal-music-architect",
        dimension=1536
    )
    container.pinecone_indexer = pinecone_indexer
    
    # 8. Initialize Semantic Service
    semantic_service = SemanticService(
        repo=container.repo,
        embedding_service=container.embedding_service,
        pinecone_indexer=container.pinecone_indexer
    )
    container.semantic_service = semantic_service

    # 9. Build graph
    graph = build_music_graph(
        container.repo,
        container.sp,
        container.llm,
        container.semantic_service
    )
    container.graph = graph

    # 10. Initialize session manager
    container.session = SessionManager(
        graph=container.graph,
        llm=container.llm,
        repo=container.repo,
        sp=container.sp,
        semantic_service=container.semantic_service
    )

    return container