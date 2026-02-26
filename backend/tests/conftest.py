import sys
import os
from pathlib import Path
import pytest
from sqlalchemy import create_engine, text
from alembic import command
from alembic.config import Config

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings

@pytest.fixture
def database_url(monkeypatch):
    """Provides a fresh PostgreSQL database URL and applies migrations."""
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://test_user:test_password@localhost:5433/miniatures_test"
    )
    # Configure app to use this URL
    monkeypatch.setenv("DATABASE_URL", db_url)
    get_settings.cache_clear()

    # Drop schema and recreate
    engine = create_engine(db_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"))
    engine.dispose()

    # Run alembic upgrade
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", db_url)
    # silence alembic stdout optionally
    command.upgrade(alembic_config, "head")

    return db_url
