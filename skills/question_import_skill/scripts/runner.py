import csv
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

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

KP_SUBJECT_MAP = [
    (r"英文|英语|单词|词汇|字母|问候|语法|时态|句型|翻译|完形|阅读.*英|听力|口语|写作.*英|初中英语", 3),
    (r"拼音|汉字|笔画|偏旁|部首|组词|造句|成语|修辞|歇后语|初中语|高中语|语文", 2),
    (r"加[减法]|乘[除法]|四则|分数|小数|质数|倍数|约数|相反数|体积|周长|面积|三角形|正方形|长方形|几何|算数|单位换算|时间计算|数的分类", 1),
    (r"代数|方程|函数|不等式|数列|排列|组合|概率|统计|勾股|坐标系|根号|平方|立方|解方程|因式分解|二次|平面几何|立体几何|初中数", 4),
    (r"物理|力学|运动|速度|加速度|牛顿|质量|密度|浮力|压强|功|能[量]|电[压流阻容]|磁[场力]|光[学折射反]|声[学音波]|热[量力学]|原子|核|单位换算.*物理|初中物理", 5),
    (r"化学|元素|原子|分子|化学式|化学方程|化合价|酸碱|pH|溶液|沉淀|氧化|还原|电解|催化|反应|物质分类|纯净物|混合物|空气成分|金属性质|初中化学", 6),
    (r"古诗|诗词|唐诗|宋词|文言文|古文|文学[常识人物]|名著|阅读.*理[解析]|作文|写[作法]|修辞|病句|标点|诗经|论语|四大名著|初中语|高中语", 8),
    (r"物理|力学|运动|速度|加速|牛顿|质量|密度|浮力|压强|电[压流阻容场]|磁[场力]|光[学折射反]|声[学音波]|热[量力学]|原子|核|量子|相对论|波动|振动|万有引力|动量|能量守恒|物理单位|高中物理", 9),
    (r"化学|元素周期|有机|无机|化学键|分子结构|晶体|化学平衡|电离|水解|电化学|热化学|反应速率|化学实验|摩尔|物质的量|高中化学", 10),
    (r"生物|细胞|基因|DNA|RNA|蛋白质|酶|光合|呼吸|遗传|进化|生态|种群|群落|免疫|神经|激素|生物分类|血液|人体|高中生物", 11),
    (r"数学|函数|导数|积分|极限|向量|复数|排列|组合|概率|统计|数列|三角|解析几何|立体几何|不等式|矩阵|算法|高中数", 12),
    (r"地理|地球|气候|地形|河流|湖泊|海洋|国家|省份|城市|人口|资源|地图|经纬|天文[常识]|太阳系|行星|地球结构|水资源|世界地理|中国地理|民族分布|地球内部", 13),
    (r"历史|朝代|皇帝|战争|革命|改革|古代|近代|现代|文明|考古|历史人物|中国历史|中国古代科技", 13),
    (r"政治|宪法|法律|制度|政府|国家|国际|联合国|人权|公民|民主|政治制度|国际政治", 13),
    (r"计算机|电脑|编程|代码|算法|网络|互联网|数据[库结构]|软件|硬件|信息技术|比特|字节", 13),
    (r"自然|常识|百科|生活|健康|安全|交通|环保|能源|天文|太阳|月亮|地球[^结构]|谚语", 13),
]


def _classify_kp(kp_name: str) -> int:
    for pattern, subject_id in KP_SUBJECT_MAP:
        if re.search(pattern, kp_name):
            return subject_id
    return 13


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
    subject_id = arguments.get("subject_id")
    if subject_id is not None:
        subject_id = int(subject_id)
    dry_run = arguments.get("dry_run", False)

    if not csv_path.exists():
        return {"ok": False, "error": f"文件不存在: {csv_path}"}

    project_root = workspace.parent
    sys.path.insert(0, str(project_root))
    from db.connection import set_db_path, get_db_connection
    set_db_path(str(project_root / "EduSupervisor.db"))

    conn = get_db_connection()
    subject_names = dict(conn.execute("SELECT id, name FROM subjects").fetchall())

    imported = 0
    skipped = 0
    errors: list[dict] = []
    new_kps: set[str] = set()
    subject_counts: dict[str, int] = defaultdict(int)

    try:
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

                sid = _classify_kp(kp_name) if subject_id is None else subject_id
                subj_name = subject_names.get(sid, f"学科{sid}")
                subject_counts[subj_name] += 1

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
                    (kp_name, sid),
                ).fetchone()
                if kp_row:
                    kp_id = kp_row[0]
                else:
                    if dry_run:
                        errors.append({"row": row_idx, "reason": f"知识点 '{kp_name}' 未找到(→{subj_name})"})
                        skipped += 1
                        continue
                    cursor = conn.execute(
                        "INSERT INTO knowledge_points (subject_id, name) VALUES (?, ?)",
                        (sid, kp_name),
                    )
                    kp_id = cursor.lastrowid
                    new_kps.add(f"{kp_name}→{subj_name}")

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
            "subjects_distribution": dict(subject_counts),
            "classify_mode": "auto" if subject_id is None else f"manual(subject_id={subject_id})",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    ws = Path(sys.argv[2])
    result = run(args, ws)
    print(json.dumps(result, ensure_ascii=False))
