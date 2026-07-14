import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from db.connection import set_db_path, get_db_connection, close_db_connection


def init_db(db_path: str | Path = None) -> None:
    if db_path is None:
        db_path = project_root / "EduSupervisor.db"
    else:
        db_path = Path(db_path)

    set_db_path(str(db_path))

    schema_path = project_root / "db" / "schema.sql"
    if not schema_path.exists():
        print(f"[ERROR] schema.sql not found: {schema_path}")
        sys.exit(1)

    schema_sql = schema_path.read_text(encoding="utf-8")

    conn = get_db_connection()
    conn.executescript(schema_sql)
    conn.commit()

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()

    print(f"[OK] 数据库初始化完成: {db_path}")
    print(f"[INFO] 已创建 {len(tables)} 张表:")
    for t in tables:
        print(f"  - {t[0]}")

    close_db_connection()


if __name__ == "__main__":
    init_db()
