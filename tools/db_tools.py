import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from db.connection import get_db_connection


def db_list_subjects() -> dict:
    try:
        conn = get_db_connection()
        rows = conn.execute("SELECT id, name, description FROM subjects ORDER BY id").fetchall()
        subjects = [{"id": r[0], "name": r[1], "description": r[2]} for r in rows]
        return {"ok": True, "subjects": subjects, "count": len(subjects)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def db_list_knowledge_points(subject_id: int) -> dict:
    try:
        conn = get_db_connection()
        rows = conn.execute(
            """SELECT id, parent_kp_id, name, description, difficulty, level, order_index
               FROM knowledge_points WHERE subject_id = ? ORDER BY level, order_index""",
            (subject_id,),
        ).fetchall()
        kps = [
            {"id": r[0], "parent_kp_id": r[1], "name": r[2],
             "description": r[3], "difficulty": r[4], "level": r[5], "order_index": r[6]}
            for r in rows
        ]
        return {"ok": True, "knowledge_points": kps, "count": len(kps)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def db_get_question(question_id: int) -> dict:
    try:
        conn = get_db_connection()
        row = conn.execute(
            """SELECT q.id, q.kp_id, kp.name as kp_name,
                      q.question_type, q.content, q.options,
                      q.answer, q.explanation, q.difficulty, q.source
               FROM questions q
               JOIN knowledge_points kp ON q.kp_id = kp.id
               WHERE q.id = ?""",
            (question_id,),
        ).fetchone()
        if row is None:
            return {"ok": False, "error": f"题目 {question_id} 不存在"}
        return {
            "ok": True,
            "question": {
                "id": row[0], "kp_id": row[1], "kp_name": row[2],
                "type": row[3], "content": row[4], "options": row[5],
                "answer": row[6], "explanation": row[7],
                "difficulty": row[8], "source": row[9],
            },
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def db_search_questions(keyword: str, limit: int = 20) -> dict:
    try:
        conn = get_db_connection()
        rows = conn.execute(
            """SELECT q.id, q.kp_id, kp.name as kp_name,
                      q.question_type, q.content, q.difficulty
               FROM questions q
               JOIN knowledge_points kp ON q.kp_id = kp.id
               WHERE q.content LIKE ? OR kp.name LIKE ?
               ORDER BY q.difficulty LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()
        questions = [
            {"id": r[0], "kp_id": r[1], "kp_name": r[2],
             "type": r[3], "content": r[4], "difficulty": r[5]}
            for r in rows
        ]
        return {"ok": True, "questions": questions, "count": len(questions)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def db_get_mastery_score(kp_id: int) -> dict:
    try:
        conn = get_db_connection()
        row = conn.execute(
            """SELECT score, confidence, last_practiced, review_count, next_review_date
               FROM mastery_scores WHERE kp_id = ?""",
            (kp_id,),
        ).fetchone()
        if row is None:
            return {"ok": True, "mastery": {"kp_id": kp_id, "score": 0.0, "is_new": True}}
        return {
            "ok": True,
            "mastery": {
                "kp_id": kp_id, "score": row[0], "confidence": row[1],
                "last_practiced": row[2], "review_count": row[3],
                "next_review_date": row[4],
            },
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def db_get_mistake_count(kp_id: int) -> dict:
    try:
        conn = get_db_connection()
        row = conn.execute(
            """SELECT COUNT(*) as total,
                      SUM(CASE WHEN resolved = 0 THEN 1 ELSE 0 END) as unresolved
               FROM mistake_log m
               JOIN questions q ON m.question_id = q.id
               WHERE q.kp_id = ?""",
            (kp_id,),
        ).fetchone()
        return {"ok": True, "kp_id": kp_id, "total_mistakes": row[0], "unresolved": row[1] or 0}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def db_get_recent_sessions(limit: int = 5) -> dict:
    try:
        conn = get_db_connection()
        rows = conn.execute(
            """SELECT id, started_at, ended_at, total_questions, correct_count, mode
               FROM study_sessions ORDER BY started_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        sessions = [
            {"id": r[0], "started_at": r[1], "ended_at": r[2],
             "total_questions": r[3], "correct_count": r[4], "mode": r[5]}
            for r in rows
        ]
        return {"ok": True, "sessions": sessions, "count": len(sessions)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
