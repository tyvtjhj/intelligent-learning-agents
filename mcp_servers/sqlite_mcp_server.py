import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = None

ALLOWED_READ_TABLES = [
    "subjects", "knowledge_points", "questions", "question_tags",
    "study_sessions", "practice_records", "mistake_log",
    "mastery_scores", "study_reports",
]
ALLOWED_WRITE_TABLES = [
    "practice_records", "mistake_log", "mastery_scores", "study_sessions",
]
FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "UPDATE", "ALTER", "CREATE", "ATTACH", "DETACH"]


def _safe_sql(sql: str, write: bool = False) -> None:
    sql_upper = sql.upper().strip()
    for kw in FORBIDDEN_KEYWORDS:
        if kw in sql_upper:
            raise ValueError(f"禁止的 SQL 操作: {kw}")
    first_word = sql_upper.split()[0]
    if write and first_word != "INSERT":
        raise ValueError("写入模式只允许 INSERT")
    if not write and first_word != "SELECT":
        raise ValueError("只读模式只允许 SELECT")


def self_mcp_complex_query(sql: str) -> str:
    _safe_sql(sql, write=False)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in conn.execute(sql).fetchall()]
        result = {"ok": True, "rows": rows, "count": len(rows)}
    except Exception as e:
        result = {"ok": False, "error": str(e)}
    finally:
        conn.close()
    return json.dumps(result, ensure_ascii=False)


def self_mcp_batch_insert(table: str, rows_json: str) -> str:
    if table not in ALLOWED_WRITE_TABLES:
        return json.dumps({"ok": False, "error": f"不允许写入表: {table}"})
    rows = json.loads(rows_json)
    if not rows:
        return json.dumps({"ok": False, "error": "rows 为空"})
    columns = list(rows[0].keys())
    placeholders = ", ".join(["?"] * len(columns))
    cols_str = ", ".join(columns)
    sql = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})"
    _safe_sql(sql, write=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        for row in rows:
            conn.execute(sql, list(row.values()))
        conn.commit()
        result = {"ok": True, "inserted": len(rows)}
    except Exception as e:
        result = {"ok": False, "error": str(e)}
    finally:
        conn.close()
    return json.dumps(result, ensure_ascii=False)


def self_mcp_export_query(sql: str, fmt: str = "json") -> str:
    _safe_sql(sql, write=False)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in conn.execute(sql).fetchall()]
        result = {"ok": True, "rows": rows, "count": len(rows), "format": fmt}
    except Exception as e:
        result = {"ok": False, "error": str(e)}
    finally:
        conn.close()
    return json.dumps(result, ensure_ascii=False)


_HANDLERS = {
    "self_mcp_complex_query": self_mcp_complex_query,
    "self_mcp_batch_insert": self_mcp_batch_insert,
    "self_mcp_export_query": self_mcp_export_query,
}


def main():
    global DB_PATH
    DB_PATH = sys.argv[1] if len(sys.argv) > 1 else None
    if DB_PATH is None:
        db = Path(__file__).parent.parent / "EduSupervisor.db"
        DB_PATH = str(db)
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            req = json.loads(line.strip())
            method = req.get("method", "")
            if method == "tools/list":
                tools = [
                    {"name": k, "description": v.__doc__ or ""}
                    for k, v in _HANDLERS.items()
                ]
                print(json.dumps({"tools": tools}, ensure_ascii=False), flush=True)
            elif method == "tools/call":
                tool_name = req.get("params", {}).get("name", "")
                arguments = req.get("params", {}).get("arguments", {})
                handler = _HANDLERS.get(tool_name)
                if handler:
                    result = handler(**arguments)
                    print(result, flush=True)
                else:
                    print(json.dumps({"ok": False, "error": f"未知工具: {tool_name}"}, ensure_ascii=False), flush=True)
        except Exception as e:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
