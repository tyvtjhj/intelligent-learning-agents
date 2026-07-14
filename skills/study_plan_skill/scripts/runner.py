import json
import sys
from pathlib import Path
from datetime import datetime, timedelta


def run(arguments: dict, workspace: Path) -> dict:
    subject_id = arguments.get("subject_id")
    days = arguments.get("days", 7)

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
            f"SELECT kp.id, kp.name, kp.difficulty, kp.level, "
            f"COALESCE(ms.score, 0) as score "
            f"FROM knowledge_points kp "
            f"LEFT JOIN mastery_scores ms ON kp.id = ms.kp_id "
            f"{where} ORDER BY COALESCE(ms.score, 0) ASC",
            params,
        ).fetchall()

        weak_kps = [
            {"id": r[0], "name": r[1], "difficulty": r[2], "level": r[3], "score": round(r[4] * 100, 1)}
            for r in rows if r[4] < 0.8
        ]

        per_day = max(1, len(weak_kps) // days)
        report_lines = [
            "# 个性化学习计划",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"计划周期: {days} 天",
            f"待复习知识点: {len(weak_kps)} 个",
            "",
        ]

        for d in range(days):
            start = d * per_day
            end = min(start + per_day, len(weak_kps))
            day_date = (datetime.now() + timedelta(days=d)).strftime("%m/%d")
            report_lines.append(f"## Day {d+1} ({day_date})")
            for kp in weak_kps[start:end]:
                report_lines.append(f"- **{kp['name']}** (掌握度: {kp['score']}%, 难度: {kp['difficulty']})")
            report_lines.append(f"  推荐练习题: {end - start} 道, 预计用时: {(end - start) * 3} 分钟\n")

        report_path = workspace / "reports" / f"study_plan_{datetime.now().strftime('%Y%m%d')}.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("\n".join(report_lines), encoding="utf-8")

        return {
            "ok": True, "report_path": str(report_path),
            "weak_kp_count": len(weak_kps), "days": days,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    ws = Path(sys.argv[2])
    result = run(args, ws)
    print(json.dumps(result, ensure_ascii=False))
