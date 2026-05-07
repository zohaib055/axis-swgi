from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from .db_url import normalize_sqlalchemy_url


def run_migrations(database_url: str) -> None:
    project_root = Path(__file__).resolve().parents[1]
    sqlalchemy_url = normalize_sqlalchemy_url(database_url)
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "migrations"))
    config.set_main_option("sqlalchemy.url", sqlalchemy_url)
    command.upgrade(config, "head")
