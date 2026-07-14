# 题目批量导入 Skill — question_import_skill

## 功能概述
将 CSV 格式的题库文件批量导入到 SQLite 数据库，自动校验格式、去重、建立知识点关联。
**支持灵活列名**：`knowledge_point`/`question`/`answer` 和 `kp_name`/`content`/`answer` 均可识别。
**调用参数**: csv_path(文件路径,必填), subject_id(学科ID,必填), dry_run(仅校验,选填)。

## 适用场景
- 学生从外部题库批量导入题目
- 初始化或扩充 Agent 的题库

## 不适用场景
- 手动逐题输入

## CSV 格式要求
必填至少包含以下三列（列名灵活）：
| 列名别名 | 说明 |
|----------|------|
| kp_name / knowledge_point / 知识点 | 知识点名称 |
| content / question / 题目 | 题目内容 |
| answer / 答案 | 正确答案 |

选填列：
| 列名别名 | 说明 |
|----------|------|
| options / 选项 | 选项（用 `|` 或空格分隔） |
| question_type / 题型 | choice/fill/true_false/short_answer/essay（不填则自动推断） |
| explanation / 解析 | 题目解析 |
| difficulty / 难度 | easy/medium/hard（默认 medium） |
| tags / 标签 | 逗号分隔标签 |

## 默认导入路径
**学生 CSV 文件默认放在 `imports/mistakes/` 目录下**，如：
- `imports/mistakes/cuoti1.csv`
- `imports/mistakes/物理错题.csv`

调用时 `csv_path` 填相对于项目根目录的路径即可。

## 自动学科归类
**subject_id 现在是可选的**：不传则根据每条题目的知识点名称自动匹配学科。
- "加法基础" → 小学数学, "唐诗" → 初中语文, "化学式" → 初中化学, "天文常识" → 通用知识
- 返回结果包含 `subjects_distribution` 显示各学科分布
- 如传 subject_id 则所有题目统一归入指定学科

## 输入参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| csv_path | string | 是 | CSV 文件路径（如 `imports/mistakes/cuoti1.csv`） |
| subject_id | integer | 否 | 目标学科 ID（不传=自动分类，传了=统一归入） |
| dry_run | boolean | 否 | 仅校验不写入(默认false) |
