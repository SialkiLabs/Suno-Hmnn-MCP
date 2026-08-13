import sqlite3
import os
from pathlib import Path
from datetime import datetime

DB_PATH = Path(os.getenv("SUNO_OUTPUT_DIR", r"C:\Users\Getko\hermy-hq\music-outputs")) / "studio_os.db"

class StudioDatabase:
    """Enterprise-grade local state manager for tracking all generations and files."""
    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()

    def _init_db(self):
        """Creates the schema if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tracks (
                    clip_id TEXT PRIMARY KEY,
                    title TEXT,
                    prompt TEXT,
                    tags TEXT,
                    model_version TEXT,
                    status TEXT,
                    created_at TIMESTAMP,
                    audio_url TEXT,
                    local_path TEXT
                )
            ''')
            conn.commit()

    def log_generation(self, clip_id: str, title: str, prompt: str, tags: str, model_version: str):
        """Logs a newly generated track to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO tracks 
                (clip_id, title, prompt, tags, model_version, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'queued', ?)
            ''', (clip_id, title, prompt, tags, model_version, datetime.now().isoformat()))
            conn.commit()

    def update_track_status(self, clip_id: str, status: str, audio_url: str = None, local_path: str = None):
        """Updates the status and file locations of an existing track."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if audio_url and local_path:
                cursor.execute('UPDATE tracks SET status=?, audio_url=?, local_path=? WHERE clip_id=?', 
                             (status, audio_url, local_path, clip_id))
            else:
                cursor.execute('UPDATE tracks SET status=? WHERE clip_id=?', (status, clip_id))
            conn.commit()

    def get_track(self, clip_id: str) -> dict:
        """Retrieves track history for the AI to read."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tracks WHERE clip_id=?', (clip_id,))
            row = cursor.fetchone()
            return dict(row) if row else {}

# Singleton instance
db = StudioDatabase()
