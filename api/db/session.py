from __future__ import annotations

import os
import json
from contextlib import contextmanager
from typing import Generator

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "database.json"

config_data = {}
if CONFIG_PATH.exists():
    try:
        config_data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        config_data = {}


def _config_value(key: str, env_name: str, default: str) -> str:
    return os.getenv(env_name) or str(config_data.get(key, default))


POSTGRES_HOST = _config_value("host", "POSTGRES_HOST", "localhost")
POSTGRES_PORT = _config_value("port", "POSTGRES_PORT", "5432")
POSTGRES_DB = _config_value("database", "POSTGRES_DB", "bogota_traffic")
POSTGRES_USER = _config_value("user", "POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = _config_value("password", "POSTGRES_PASSWORD", "postgres")

DEFAULT_DATABASE_URL = config_data.get("url") or (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

DATABASE_URL = os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL

engine_kwargs = {
    "pool_pre_ping": True,
    "future": True,
}

if DATABASE_URL.startswith("sqlite"):
    # Permitir uso en hilos múltiples durante tests
    engine_kwargs["connect_args"] = {"check_same_thread": False}


engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
