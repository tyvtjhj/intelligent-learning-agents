import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import set_db_path, get_db_connection

project_root = Path(__file__).parent.parent
db_path = str(project_root / "EduSupervisor.db")
set_db_path(db_path)
conn = get_db_connection()

conn.execute("INSERT INTO subjects (id, name, description) VALUES (1, '初中数学', '初中数学知识点体系')")
conn.execute("INSERT INTO subjects (id, name, description) VALUES (2, '初中物理', '初中物理知识点体系')")

kps = [
    (1, 1, None, '有理数', '整数和分数的统称', 'easy', 0, 1),
    (2, 1, None, '一元一次方程', '含有一个未知数且未知数最高次数为1的方程', 'medium', 0, 2),
    (3, 1, None, '平面直角坐标系', '由两条互相垂直的数轴构成的坐标系', 'medium', 0, 3),
    (4, 1, 1, '正数和负数', '大于0和小于0的数', 'easy', 1, 1),
    (5, 1, 1, '绝对值', '数轴上的点到原点的距离', 'medium', 1, 2),
    (6, 1, 2, '解一元一次方程', '移项、合并同类项、系数化1', 'medium', 1, 1),
    (7, 1, 2, '一元一次方程应用题', '用方程解决实际问题', 'hard', 1, 2),
    (8, 2, None, '声现象', '声音的产生与传播', 'easy', 0, 1),
    (9, 2, None, '光现象', '光的传播与反射折射', 'medium', 0, 2),
    (10, 2, 8, '声音的特性', '音调、响度、音色', 'easy', 1, 1),
]

for kp in kps:
    conn.execute(
        "INSERT INTO knowledge_points (id, subject_id, parent_kp_id, name, description, difficulty, level, order_index) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        kp,
    )

questions = [
    (1, 1, 'choice', '|-5| 的值是多少？', '["A. -5", "B. 5", "C. 0", "D. 1"]', 'B', '绝对值表示数轴上的点到原点的距离，总是非负的。', 'easy'),
    (2, 1, 'fill', '计算：(-3) + 8 = ____', None, '5', '异号两数相加，取绝对值较大的符号，并用较大的绝对值减去较小的绝对值。', 'easy'),
    (3, 2, 'choice', '下列哪个是一元一次方程？', '["A. x²+1=0", "B. 2x+3=7", "C. x+y=5", "D. 1/x=2"]', 'B', '一元一次方程只有一个未知数，且未知数的最高次数为1。', 'easy'),
    (4, 2, 'fill', '解方程：3x - 7 = 2x + 3，x = ____', None, '10', '移项：3x-2x=3+7，合并：x=10。', 'medium'),
    (5, 5, 'choice', '若 |a| = 3，则 a 的值是？', '["A. 3", "B. -3", "C. ±3", "D. 0"]', 'C', '绝对值为3的数有两个：3和-3。', 'medium'),
    (6, 5, 'true_false', '|a| = |-a| 总是成立。', None, 'true', '一个数和它的相反数的绝对值相等。', 'easy'),
    (7, 7, 'choice', '小明买了3支笔和2个本子花了19元，已知本子5元一个，笔多少钱一支？', '["A. 2元", "B. 3元", "C. 4元", "D. 5元"]', 'B', '设笔x元，3x+2×5=19，3x=9，x=3。', 'medium'),
    (8, 10, 'choice', '调节电视机音量，改变的是声音的什么特性？', '["A. 音调", "B. 响度", "C. 音色", "D. 频率"]', 'B', '音量大小对应响度。音调由频率决定，音色由发声体材料结构决定。', 'easy'),
    (9, 8, 'choice', '声音在下列哪种介质中传播最快？', '["A. 空气", "B. 水", "C. 钢铁", "D. 真空"]', 'C', '声音传播速度：固体 > 液体 > 气体，真空中不能传声。', 'medium'),
    (10, 9, 'true_false', '光在同种均匀介质中沿直线传播。', None, 'true', '光在同种均匀介质中沿直线传播，这是几何光学的基本假设。', 'easy'),
]

for q in questions:
    conn.execute(
        "INSERT INTO questions (id, kp_id, question_type, content, options, answer, explanation, difficulty) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        q,
    )

print("[OK] 种子数据已导入")
print(f"  学科: 2 个 (初中数学, 初中物理)")
print(f"  知识点: {len(kps)} 个")
print(f"  题目: {len(questions)} 道")
conn.commit()
conn.close()
