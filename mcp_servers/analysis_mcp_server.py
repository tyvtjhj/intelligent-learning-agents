import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = None


def self_mcp_learning_stats(subject_id: int) -> str:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """SELECT kp.name, ms.score
               FROM mastery_scores ms
               JOIN knowledge_points kp ON ms.kp_id = kp.id
               WHERE kp.subject_id = ?
               ORDER BY ms.score ASC""",
            (subject_id,),
        ).fetchall()
        radar = [{"name": r["name"], "score": round((r["score"] or 0) * 100, 1)} for r in rows]
        result = {"ok": True, "kps": radar, "count": len(radar)}
    except Exception as e:
        result = {"ok": False, "error": str(e)}
    finally:
        conn.close()
    return json.dumps(result, ensure_ascii=False)


def self_mcp_weak_point_ranking(subject_id: int, top_n: int = 10) -> str:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """SELECT kp.id, kp.name, ms.score,
                      (SELECT COUNT(*) FROM mistake_log ml
                       JOIN questions q ON ml.question_id = q.id
                       WHERE q.kp_id = kp.id AND ml.resolved = 0) as unresolved_errors
               FROM knowledge_points kp
               LEFT JOIN mastery_scores ms ON kp.id = ms.kp_id
               WHERE kp.subject_id = ?
               ORDER BY COALESCE(ms.score, 0) ASC, unresolved_errors DESC
               LIMIT ?""",
            (subject_id, top_n),
        ).fetchall()
        ranking = [
            {"kp_id": r["id"], "name": r["name"],
             "score": round((r["score"] or 0) * 100, 1),
             "unresolved_errors": r["unresolved_errors"] or 0}
            for r in rows
        ]
        result = {"ok": True, "ranking": ranking}
    except Exception as e:
        result = {"ok": False, "error": str(e)}
    finally:
        conn.close()
    return json.dumps(result, ensure_ascii=False)


def self_mcp_mastery_trend(kp_id: int) -> str:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT score, confidence, last_practiced, review_count FROM mastery_scores WHERE kp_id = ?",
            (kp_id,),
        ).fetchone()
        if row is None:
            result = {"ok": True, "trend": {"kp_id": kp_id, "score": 0.0, "is_new": True}}
        else:
            result = {"ok": True, "trend": {
                "kp_id": kp_id, "score": round((row["score"] or 0) * 100, 1),
                "confidence": round((row["confidence"] or 0) * 100, 1),
                "last_practiced": row["last_practiced"], "review_count": row["review_count"],
            }}
    except Exception as e:
        result = {"ok": False, "error": str(e)}
    finally:
        conn.close()
    return json.dumps(result, ensure_ascii=False)


_HANDLERS = {
    "self_mcp_learning_stats": self_mcp_learning_stats,
    "self_mcp_weak_point_ranking": self_mcp_weak_point_ranking,
    "self_mcp_mastery_trend": self_mcp_mastery_trend,
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
                tools = [{"name": k, "description": v.__doc__ or ""} for k, v in _HANDLERS.items()]
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
