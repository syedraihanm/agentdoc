import sqlite3
from pathlib import Path
from contextlib import contextmanager
from backend.app.config import settings

def get_db_path() -> Path:
    settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return settings.DB_PATH

def init_db(db_path: Path | None = None) -> None:
    path = db_path or get_db_path()
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = f.read()
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(schema)
    conn.commit()
    conn.close()

@contextmanager
def get_db(db_path: Path | None = None):
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
