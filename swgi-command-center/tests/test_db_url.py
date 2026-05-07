from __future__ import annotations

from app.db_url import normalize_psycopg_dsn, normalize_sqlalchemy_url


def test_normalizes_psycopg2_url_for_runtime_psycopg() -> None:
    url = "postgresql+psycopg2://user:pass@example.com:5432/db"

    assert normalize_psycopg_dsn(url) == "postgresql://user:pass@example.com:5432/db"


def test_normalizes_urls_for_alembic_sqlalchemy_psycopg() -> None:
    assert (
        normalize_sqlalchemy_url("postgresql+psycopg2://user:pass@example.com:5432/db")
        == "postgresql+psycopg://user:pass@example.com:5432/db"
    )
    assert (
        normalize_sqlalchemy_url("postgresql://user:pass@example.com:5432/db")
        == "postgresql+psycopg://user:pass@example.com:5432/db"
    )
