"""Local track records. Database creation is deferred until first use."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from .paths import database_path


class StudioDatabase:
    def __init__(self, db_path: Path | None = None):
        self.db_path = Path(db_path) if db_path is not None else None

    @contextmanager
    def _connect(self):
        path = self.db_path or database_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path, timeout=10)
        try:
            conn.execute("""CREATE TABLE IF NOT EXISTS tracks (
            clip_id TEXT PRIMARY KEY, title TEXT, prompt TEXT, tags TEXT,
            model_version TEXT, status TEXT, created_at TIMESTAMP,
            audio_url TEXT, local_path TEXT)""")
            with conn:
                yield conn
        finally:
            conn.close()

    def log_generation(self, clip_id, title, prompt, tags, model_version):
        if not clip_id:
            raise ValueError("A clip ID is required")
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO tracks
                (clip_id,title,prompt,tags,model_version,status,created_at)
                VALUES (?,?,?,?,?,'queued',?)
                ON CONFLICT(clip_id) DO UPDATE SET title=excluded.title,
                    prompt=excluded.prompt,tags=excluded.tags,model_version=excluded.model_version""",
                (
                    clip_id,
                    title,
                    prompt,
                    tags,
                    model_version,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def update_track_status(self, clip_id, status, audio_url=None, local_path=None):
        with self._connect() as conn:
            conn.execute(
                """UPDATE tracks SET status=?, audio_url=COALESCE(?,audio_url),
                local_path=COALESCE(?,local_path) WHERE clip_id=?""",
                (status, audio_url, local_path, clip_id),
            )

    def get_track(self, clip_id):
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM tracks WHERE clip_id=?", (clip_id,)
            ).fetchone()
            return dict(row) if row else {}

    def list_tracks(self, limit=50):
        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or not 1 <= limit <= 500
        ):
            raise ValueError("limit must be an integer between 1 and 500")
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            return [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM tracks ORDER BY created_at DESC LIMIT ?", (limit,)
                )
            ]


db = StudioDatabase()
