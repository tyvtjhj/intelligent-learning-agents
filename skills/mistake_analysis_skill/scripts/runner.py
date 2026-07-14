import json
import sys
from pathlib import Path
from datetime import datetime


def run(arguments: dict, workspace: Path) -> dict:
    subject_id = arguments.get("subject_id")
    limit = arguments.get("limit", 50)

    project_root = workspace.parent
    sys.path.insert(0, str(project_root))
    from db.connection import set_db_path, get_db_connection
    set_db_path(str(project_root / "EduSupervisor.db"))

    try:
        conn = get_db_connection()

        where = "WHERE 1=1"
        params: list = []
        if subject_id is not None:
            where += " AND kp.subject_id = ?"
            params.append(int(subject_id))

        rows = conn.execute(
            f"""SELECT kp.id, kp.name, COUNT(ml.id) as mistake_count,
                       SUM(CASE WHEN ml.resolved = 0 THEN 1 ELSE 0 END) as unresolved
                FROM mistake_log ml
                JOIN questions q ON ml.question_id = q.id
                JOIN knowledge_points kp ON q.kp_id = kp.id
                {where}
                GROUP BY kp.id
                ORDER BY unresolved DESC, mistake_count DESC
                LIMIT ?""",
            params + [int(limit)],
        ).fetchall()

        detail_rows = conn.execute(
            f"""SELECT ml.id, q.content, ml.student_answer, ml.correct_answer, ml.error_type, kp.name
                FROM mistake_log ml
                JOIN questions q ON ml.question_id = q.id
                JOIN knowledge_points kp ON q.kp_id = kp.id
                {where}
                ORDER BY ml.created_at DESC LIMIT ?""",
            params + [int(limit)],
        ).fetchall()

        report_lines = [
            "# 错题分析报告",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## 薄弱知识点排名",
        ]
        for i, r in enumerate(rows, 1):
            report_lines.append(
                f"{i}. **{r[1]}** — 错题 {r[2]} 次, 未解决 {r[3]} 次"
            )

        report_lines.append("\n## 错题详情")
        for r in detail_rows:
            report_lines.append(
                f"- [{r[5]}] {r[1][:80]}\n"
                f"  你的答案: {r[2][:60]} | 正确答案: {r[3][:60]}"
            )

        report_path = workspace / "reports" / f"mistake_analysis_{datetime.now().strftime('%Y%m%d')}.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("\n".join(report_lines), encoding="utf-8")

        return {
            "ok": True, "report_path": str(report_path),
            "weak_kps": [{"name": r[1], "mistakes": r[2], "unresolved": r[3]} for r in rows],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    ws = Path(sys.argv[2])
    result = run(args, ws)
    print(json.dumps(result, ensure_ascii=False))
