import json
import sys
from pathlib import Path
from datetime import datetime, timedelta


def run(arguments: dict, workspace: Path) -> dict:
    subject_id = arguments.get("subject_id")
    days = arguments.get("days", 30)

    project_root = workspace.parent
    sys.path.insert(0, str(project_root))
    from db.connection import set_db_path, get_db_connection
    set_db_path(str(project_root / "EduSupervisor.db"))

    try:
        conn = get_db_connection()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        where = ""
        params: list = []
        if subject_id is not None:
            where = "WHERE kp.subject_id = ?"
            params.append(int(subject_id))

        kp_rows = conn.execute(
            f"SELECT kp.id, kp.name, ms.score FROM knowledge_points kp "
            f"LEFT JOIN mastery_scores ms ON kp.id = ms.kp_id {where} ORDER BY ms.score ASC NULLS FIRST",
            params,
        ).fetchall()

        total_rows = conn.execute(
            f"SELECT COUNT(*) FROM practice_records pr "
            f"JOIN questions q ON pr.question_id = q.id "
            f"JOIN knowledge_points kp ON q.kp_id = kp.id {where}",
            params,
        ).fetchone()

        correct_rows = conn.execute(
            f"SELECT COUNT(*) FROM practice_records pr "
            f"JOIN questions q ON pr.question_id = q.id "
            f"JOIN knowledge_points kp ON q.kp_id = kp.id "
            f"{'AND' if where else 'WHERE'} pr.is_correct = 1" + (f" AND kp.subject_id = ?" if where else ""),
            params + ([int(subject_id)] if subject_id is not None else []),
        ).fetchone()

        total = total_rows[0] if total_rows else 0
        correct = correct_rows[0] if correct_rows else 0

        kps = [{"id": r[0], "name": r[1], "score": round((r[2] or 0) * 100, 1)} for r in kp_rows]

        report_lines = [
            "# 学习报告",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"统计周期: 最近 {days} 天",
            "",
            "## 总体数据",
            f"- 总练习量: {total}",
            f"- 正确数: {correct}",
            f"- 正确率: {correct/total*100:.1f}%" if total > 0 else "- 正确率: N/A",
            "",
            "## 知识点掌握度",
        ]
        for kp in kps:
            bar = "█" * int(kp["score"] / 5) + "░" * (20 - int(kp["score"] / 5))
            report_lines.append(f"- {kp['name']}: {kp['score']}% {bar}")

        report_path = workspace / "reports" / f"learning_report_{datetime.now().strftime('%Y%m%d')}.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("\n".join(report_lines), encoding="utf-8")

        return {"ok": True, "report_path": str(report_path), "total_practice": total, "kp_count": len(kps)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    ws = Path(sys.argv[2])
    result = run(args, ws)
    print(json.dumps(result, ensure_ascii=False))
