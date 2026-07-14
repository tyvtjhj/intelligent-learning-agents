import csv
import json
import sys
from pathlib import Path

COLUMN_ALIASES = {
    "kp_name": ["kp_name", "knowledge_point", "知识点", "kp", "topic"],
    "content": ["content", "question", "题目", "problem", "title"],
    "answer": ["answer", "答案", "correct", "正确选项"],
    "question_type": ["question_type", "type", "题型", "format"],
    "options": ["options", "选项", "choices"],
    "explanation": ["explanation", "解析", "explain", "备注"],
    "difficulty": ["difficulty", "难度", "level"],
    "tags": ["tags", "标签", "category"],
}


def _derive_question_type(content: str, options: str) -> str:
    if options and options.strip():
        return "choice"
    if any(marker in content for marker in ["___", "____"]):
        return "fill"
    return "short_answer"


def _resolve_columns(fieldnames: list[str]) -> dict[str, str | None]:
    mapping = {}
    for target, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in fieldnames:
                mapping[target] = alias
                break
        else:
            mapping[target] = None
    return mapping


def _get_row_value(row: dict, col_map: dict, target: str, default: str = "") -> str:
    alias = col_map.get(target)
    if alias is None:
        return default
    return row.get(alias, default)


def _open_csv(csv_path: Path):
    f = open(csv_path, "r", encoding="utf-8-sig")
    first_line = f.readline()
    first_columns = next(csv.reader([first_line]))
    if first_columns and all(c.lower().startswith("column") for c in first_columns if c):
        reader = csv.DictReader(f)
        col_map = _resolve_columns(list(reader.fieldnames or []))
        return reader, col_map, f
    f.seek(0)
    return csv.DictReader(f), _resolve_columns(first_columns), f


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
    errors: list[dict] = []
    new_kps: set[str] = set()

    try:
        conn = get_db_connection()

        reader, col_map, _fh = _open_csv(csv_path)

        missing_required = [t for t in ["kp_name", "content", "answer"] if col_map[t] is None]
        if missing_required:
            friendly = {
                "kp_name": "知识点名称(knowledge_point/kp_name/知识点)",
                "content": "题目内容(question/content/题目)",
                "answer": "答案(answer/答案)",
            }
            return {
                "ok": False,
                "error": f"CSV 缺少必填列，当前列: {list(reader.fieldnames or [])}。需要包含: " + ", ".join(friendly[t] for t in missing_required),
            }

        for row_idx, row in enumerate(reader, start=2):
            try:
                kp_name = _get_row_value(row, col_map, "kp_name").strip()
                content = _get_row_value(row, col_map, "content").strip()
                answer = _get_row_value(row, col_map, "answer").strip()

                for label, val in [("知识点", kp_name), ("题目", content), ("答案", answer)]:
                    if not val:
                        raise ValueError(f"必填字段 '{label}' 为空")

                raw_type = _get_row_value(row, col_map, "question_type").strip()
                raw_options = _get_row_value(row, col_map, "options").strip()

                q_type = raw_type if raw_type else _derive_question_type(content, raw_options)

                valid_types = {"choice", "fill", "true_false", "short_answer", "essay"}
                if q_type not in valid_types:
                    raise ValueError(f"无效题型: {q_type}（可选: choice/fill/true_false/short_answer/essay）")

                diff_raw = _get_row_value(row, col_map, "difficulty", "medium").strip() or "medium"
                difficulty = diff_raw if diff_raw in {"easy", "medium", "hard"} else "medium"

                dup = conn.execute(
                    "SELECT id FROM questions WHERE content = ? AND answer = ?",
                    (content, answer),
                ).fetchone()
                if dup:
                    skipped += 1
                    continue

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

                if dry_run:
                    imported += 1
                    continue

                options_val = raw_options or None
                cursor = conn.execute(
                    """INSERT INTO questions (kp_id, question_type, content, options, answer, explanation, difficulty, source)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (kp_id, q_type, content, options_val, answer,
                     _get_row_value(row, col_map, "explanation").strip() or "", difficulty, "csv_import"),
                )
                question_id = cursor.lastrowid

                tags_raw = _get_row_value(row, col_map, "tags").strip()
                if tags_raw:
                    for tag in tags_raw.split(","):
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
