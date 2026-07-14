import csv
import json
import sys
from pathlib import Path


def run(arguments: dict, workspace: Path) -> dict:
    csv_path = Path(arguments["csv_path"])
    subject_id = int(arguments["subject_id"])
    dry_run = arguments.get("dry_run", False)

    if not csv_path.exists():
        return {"ok": False, "error": f"文件不存在: {csv_path}"}

    project_root = workspace.parent
    sys.path.insert(0, str(project_root))
    from db.connection import set_db_path, get_db_connection
    set_db_path(str(project_root / "EduSupervisor.db"))

    imported = 0
    skipped = 0
    errors = []
    new_kps = set()

    try:
        conn = get_db_connection()

        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for field in ["kp_name", "question_type", "content", "answer"]:
                if field not in reader.fieldnames:
                    return {"ok": False, "error": f"CSV 缺少必填列: {field}"}

            for row_idx, row in enumerate(reader, start=2):
                try:
                    for field in ["kp_name", "question_type", "content", "answer"]:
                        if not row.get(field, "").strip():
                            raise ValueError(f"必填字段 '{field}' 为空")

                    kp_name = row["kp_name"].strip()
                    kp_row = conn.execute(
                        "SELECT id FROM knowledge_points WHERE name = ? AND subject_id = ?",
                        (kp_name, subject_id),
                    ).fetchone()
                    if kp_row:
                        kp_id = kp_row[0]
                    else:
                        if dry_run:
                            errors.append({"row": row_idx, "reason": f"知识点 '{kp_name}' 未找到"})
                            skipped += 1
                            continue
                        cursor = conn.execute(
                            "INSERT INTO knowledge_points (subject_id, name) VALUES (?, ?)",
                            (subject_id, kp_name),
                        )
                        kp_id = cursor.lastrowid
                        new_kps.add(kp_name)

                    valid_types = {"choice", "fill", "true_false", "short_answer", "essay"}
                    q_type = row["question_type"].strip()
                    if q_type not in valid_types:
                        raise ValueError(f"无效题型: {q_type}")

                    difficulty = row.get("difficulty", "medium").strip() or "medium"
                    if difficulty not in {"easy", "medium", "hard"}:
                        raise ValueError(f"无效难度: {difficulty}")

                    content = row["content"].strip()
                    answer = row["answer"].strip()
                    dup = conn.execute(
                        "SELECT id FROM questions WHERE content = ? AND answer = ?",
                        (content, answer),
                    ).fetchone()
                    if dup:
                        skipped += 1
                        continue

                    if dry_run:
                        imported += 1
                        continue

                    options = row.get("options", "").strip() or None
                    cursor = conn.execute(
                        """INSERT INTO questions (kp_id, question_type, content, options, answer, explanation, difficulty, source)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (kp_id, q_type, content, options, answer,
                         row.get("explanation", "").strip() or "", difficulty, "csv_import"),
                    )
                    question_id = cursor.lastrowid

                    tags = row.get("tags", "").strip()
                    if tags:
                        for tag in tags.split(","):
                            tag = tag.strip()
                            if tag:
                                conn.execute(
                                    "INSERT OR IGNORE INTO question_tags (question_id, tag_name) VALUES (?, ?)",
                                    (question_id, tag),
                                )

                    imported += 1
                except Exception as e:
                    errors.append({"row": row_idx, "reason": str(e)})
                    skipped += 1

        conn.commit()
        return {
            "ok": True, "imported": imported, "skipped": skipped,
            "errors": errors[:20], "new_kps_created": list(new_kps),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    ws = Path(sys.argv[2])
    result = run(args, ws)
    print(json.dumps(result, ensure_ascii=False))
