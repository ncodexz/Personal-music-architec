from core.database import get_connection


class DatabaseSession:
    def __init__(self, db_path: str = "music_agent.db"):
        self._conn = get_connection(db_path)

    @property
    def conn(self):
        return self._conn

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()