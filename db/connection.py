import sqlite3
from pathlib import Path
from threading import Lock

_connection = None
_lock = Lock()
_db_path = None


def set_db_path(path: str | Path) -> None:
    global _db_path
    _db_path = str(path)


def get_db_connection() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        with _lock:
            if _connection is None:
                if _db_path is None:
                    raise RuntimeError("db path not set, call set_db_path() first")
                _connection = sqlite3.connect(_db_path)
                _connection.row_factory = sqlite3.Row
                _connection.execute("PRAGMA journal_mode=WAL")
                _connection.execute("PRAGMA foreign_keys=ON")
    return _connection


def close_db_connection() -> None:
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
