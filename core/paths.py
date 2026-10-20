"""Resolve local storage without writing into the installed package."""

import os
from pathlib import Path
import platformdirs


def output_directory() -> Path:
    configured = os.getenv("SUNO_OUTPUT_DIR")
    root = (
        Path(configured).expanduser()
        if configured
        else Path(platformdirs.user_music_dir()) / "SunoStudio"
    )
    return root.resolve()


def database_path() -> Path:
    configured = os.getenv("SUNO_DATABASE_PATH")
    return (
        Path(configured).expanduser().resolve()
        if configured
        else output_directory() / "studio_os.db"
    )
