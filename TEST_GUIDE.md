# 小宋·教育督学 Agent 测试指南

> 使用前先运行 `python scripts/seed_data.py` 导入种子数据
> 共 35 条测试用例，覆盖 28 个全部工具

---

## 启动 Agent

```bash
cd EduSupervisor
python agent.py
```

```
============================================================
  小宋·教育督学 Agent (EduSupervisor) v1.0
  模型: deepseek-v4-pro | 工具: 28 个
  输入 'quit' 退出 | 'status' 验收进度 | 'clear' 清除上下文
============================================================
```

---

## 第一部分：本地 Tool 测试（🔧，14个）

### #1 计算器
```
> 帮我算一下 128 × 37 + 256
```
**预期触发**：🔧 `calculator` → 返回 4992

### #2 当前时间
```
> 现在几点了
```
**预期触发**：🔧 `get_current_time`

### #3 列出学科
```
> 有哪些学科
```
**预期触发**：🔧 `db_list_subjects` → 13个学科（含通用知识）

### #4 列出知识点
```
> 小学数学有哪些知识点
```
**预期触发**：🔧 `db_list_knowledge_points` → 返回学科1的知识点

### #5 搜索题目
```
> 找一下和勾股定理有关的题
```
**预期触发**：🔧 `db_search_questions`

### #6 单题详情
```
> 题目 1 的详细信息
```
**预期触发**：🔧 `db_get_question(question_id=1)`

### #7 近期学习
```
> 我最近学习情况怎么样
```
**预期触发**：🔧 `db_get_recent_sessions`

### #8 保存笔记
```
> 帮我把这段话存一下：今天学了分数加减法
```
**预期触发**：🔧 `save_text` → 写入 `workspace/learning_note_xxx.txt`

### #9 读取笔记（列文件→读文件）
```
> 读取我保存的笔记
```
**预期触发**：🔧 `read_text`（不传filename）→ 列出8个文件 → 用户选文件 → `read_text(filename="xxx")` → **读取后直接展示，不查数据库**

### #10 列出导入文件
```
> 导入题库
```
**预期触发**：🔧 `list_import_files` → 返回 `imports/mistakes/` 下CSV文件列表（如 `cuoti1.csv`, `cuoti2.csv`）

### #11 掌握度查询
```
> 知识点的掌握度怎么样
```
**预期触发**：🔧 `db_get_mastery_score`

### #12 错题数量
```
> 这个知识点有多少错题
```
**预期触发**：🔧 `db_get_mistake_count`

### #12b 出题→答错→记录错题→费曼纠错（闭环）
> 先让 Agent 出一道题，然后故意答错，验证错题入库+纠错全流程：
```
> 给我出一道小学数学加法题
```
→ Agent 出题后，学生故意回答错误：
```
> A
```
（假设正确答案不是A）
**预期触发**：🔧 `db_save_new_knowledge`(返回question_id) → 🔌 `self_mcp_batch_insert`(写mistake_log) → 📥 `external_skill_feynman_tutor`(纠错讲解)
**验证**：回答后执行 `导出错题`，CSV 应有这条错题记录

---

## 第二部分：自建 Skill 测试（📦，4个）

### #13 题库导入
> 承接 #10，"导入题库"返回文件列表后：
```
> 第一个
```
→ 用户选择 `cuoti1.csv`，Agent 调用导入
**预期触发**：📦 `skill_question_import_skill(csv_path="imports/mistakes/cuoti1.csv")` → 自动学科归类 → 返回分布

### #14 学习计划
```
> 帮我制定一个 7 天复习计划，小学数学
```
**预期触发**：📦 `skill_study_plan_skill` → `workspace/reports/study_plan_xxx.md`

### #15 学习报告
```
> 生成一份学习报告
```
**预期触发**：📦 `skill_learning_report_skill` → `workspace/reports/learning_report_xxx.md`

### #16 错题分析
```
> 分析我的错题
```
**预期触发**：📦 `skill_mistake_analysis_skill` → `workspace/reports/mistake_analysis_xxx.md`

### #16b 查看错题（区别于分析错题）
> 验证"查看错题"和"分析错题"走不同工具：
```
> 查看错题
```
**预期触发**：🔌 `self_mcp_complex_query`（只查 mistake_log 展示，**不调** skill_mistake_analysis_skill）
**区分**：`查看错题` → 只展示列表；`分析错题` → 调 Skill 生成报告

---

## 第三部分：外部 Skill 测试（📥，3个+170个Pack）

### #17 费曼教学（本地命中）
```
> 什么是光合作用
```
**预期触发**：🔧 `db_search_questions`(count>0) → 📥 `external_skill_feynman_tutor` → 费曼风格讲解（生活类比+零术语+ASCII图解）

### #18 精熟练习
```
> 给我出几道物理题考考我
```
**预期触发**：📥 `external_skill_sigma` → 布鲁姆精熟法出题

### #19 费曼教学（本地未命中→联网→入库）
```
> 用三角函数公式教我
```
**预期触发**：🔧 `db_search_questions`(count=0) → 🌐 `external_search` → 📥 `external_skill_feynman_tutor` → 🔧 `db_save_new_knowledge`

### #19b 联网入库→question_id 写错题表
> 验证 db_save_new_knowledge 返回 question_id 供后续写 mistake_log：
```
> 用三角函数公式教我，然后出一道题考考我
```
→ Agent 联网获取知识→入库→出题→学生答错
**预期触发**：🌐 `external_search` → 🔧 `db_save_new_knowledge`(返回含question_id) → 📥 `external_skill_feynman_tutor` → 出题 → 学生答错后 → 🔌 `self_mcp_batch_insert`(用前面的question_id)
**验证**：question_id 从 db_save_new_knowledge 返回值获取，不凭空编造

### #20 Hermes Edu 教材同步
```
> 用人教版数学方法教分数
```
**预期触发**：📥 `external_skill_hermes_edu` → 注入教材同步教学方法

---

## 第四部分：自建 MCP 测试（🔌，6个）

### #21 学习统计
```
> 初中物理的学习统计数据
```
**预期触发**：🔌 `self_mcp_learning_stats` → 返回雷达图数据

### #22 薄弱点排行
```
> 我最薄弱的10个知识点是哪些
```
**预期触发**：🔌 `self_mcp_weak_point_ranking` → Top N 排名

### #23 掌握度趋势
```
> 四则运算的掌握度变化趋势
```
**预期触发**：🔌 `self_mcp_mastery_trend`

### #24 复杂SQL查询
```
> 用 SQL 查一下所有选择题
```
**预期触发**：🔌 `self_mcp_complex_query`

### #25 批量插入
```
> 帮我批量插入一条练习记录
```
**预期触发**：🔌 `self_mcp_batch_insert`

### #26 导出CSV-题目（LEFT JOIN，1步完成）
```
> 导出所有数学题到 CSV，还要告诉我文件位置
```
**预期触发**：🔌 `self_mcp_export_query(sql="SELECT...LEFT JOIN...WHERE sub.name LIKE '%数学%'", fmt="csv", output="math_questions")` → `outputs/math_questions.csv` → **不逐题查，不循环**
⚠️ 导出 SQL 必须用 **LEFT JOIN**（不是 JOIN），防止 FK 断裂时静默丢行

### #26b 导出错题CSV（LEFT JOIN + 兜底SQL）
```
> 导出错题
```
**预期触发**：
1. 首先：🔌 `self_mcp_export_query(sql="SELECT m.id, q.content, ... FROM mistake_log m LEFT JOIN questions q ...", fmt="csv", output="mistakes_export")`
2. 如果第1步返回 count=0 → 兜底：🔌 `self_mcp_export_query(sql="SELECT * FROM mistake_log", fmt="csv", output="mistakes_export")`
3. 两次都返回0 → action:finish 告知"错题本是空的"
⚠️ **不要先调 complex_query 探测！直接导出+兜底即可**

---

## 第五部分：外部 MCP 测试（🌐，1个）

### #27 联网搜索
```
> 什么是量子场论
```
**预期触发**：🔧 `db_search_questions`(count=0) → 🌐 `external_search`(3次重试) → 📥 `external_skill_feynman_tutor` → 🔧 `db_list_subjects` → 🔧 `db_save_new_knowledge`

---

## 第六部分：组合场景（综合验收）

### #28 导入+复习
```
> 导入题库 → 选cuoti1.csv → 然后分析错题
```
**预期触发**：🔧 `list_import_files` → 📦 `skill_question_import_skill` → 📦 `skill_mistake_analysis_skill`

### #29 讲解+出题
```
> 先教我勾股定理，然后出几道题考我
```
**预期触发**：🔧 `db_search_questions` → 📥 `external_skill_feynman_tutor` → 📥 `external_skill_sigma`

### #30 报告+计划
```
> 生成学习报告，再帮我制定复习计划
```
**预期触发**：📦 `skill_learning_report_skill` → 📦 `skill_study_plan_skill`

### #31 status 验收
```
> status
```
**预期触发**：显示验收进度

```
# 验收进度
[✓] 本地Tool调用
[✓] 自建Skill调用
[✓] 外部Skill调用
[✓] 自建MCP调用
[✓] 外部MCP调用
```

### #32 全部独立测试
```
> 帮我算 128×37 → 现在几点了 → 有哪些学科 → 小学数学有哪些知识点 → 
  找一下和勾股定理有关的题 → 给我出几道物理题 → 什么是光合作用 → 
  生成学习报告 → 分析错题 → 帮我制定7天复习计划 → 
  导出所有数学题到CSV → status
```
**预期**：一条指令串联 12 个工具，验收全绿 ✓

---

## 快速最小覆盖（5条）

按顺序执行下面 5 句，覆盖全部 5 大知识域：

```
> 有哪些学科？
> 什么是光合作用
> 生成学习报告
> 帮我制定一个 7 天复习计划，小学数学
> 导出所有数学题到 CSV
```

| 知识域 | 工具数 | 验收 |
|--------|--------|------|
| 本地 Tool | 14 | `db_list_subjects`, `db_search_questions` 被调用 |
| 自建 Skill | 4 | `skill_learning_report_skill`, `skill_study_plan_skill` 被调用 |
| 外部 Skill | 3 | `external_skill_feynman_tutor` 被调用 |
| 自建 MCP | 6 | `self_mcp_export_query` 被调用 |
| 外部 MCP | 1 | `external_search`（仅在未命中时触发） |

---

## 常见问题排查

| 现象 | 可能原因 | 解决 |
|------|---------|------|
| Agent 回答卡住不动 | API 超时或上下文过长 | Ctrl+C 重新运行 |
| 工具未找到 | 种子数据未导入 | 运行 `python scripts/seed_data.py` |
| 外部 Skill 加载失败 | 未安装外部仓库 | 运行 `python scripts/install_external_skills.py` |
| `read_text` 反复试探参数名 | 旧版 System Prompt | 确认 ToolSpec 标注 "参数名是 filename（不是 path/file）" |
| 导出CSV 15步死循环 | Agent 不知参数名 | 确认 System Prompt 含 SQL 示例+参数名 sql/fmt/output |
| 读取笔记后额外查数据库 | Agent 误触兜底策略 | 确认 ToolSpec 标注 "读取笔记后直接展示，不查DB" |
| 本地命中知识点仍重复入库 | System Prompt 条件分支不明确 | 确认分支A规则 "count>0 → 不调 db_save_new_knowledge" |
| 导出错题CSV返回空文件 | INNER JOIN FK链断裂静默丢行 | 确认导出 SQL 用 LEFT JOIN + COALESCE 兜底空值 |
| 答错题后错题本还是空的 | Agent 跳过入库直接讲解 | 确认 System Prompt 含 "错题记录" 规则：入库→写mistake_log→再讲解 |
| `.format()` 报 `KeyError: "question_id"` | 错题记录规则中的 JSON 花括号被 Python format 解析 | 确认 `core/agent.py` 用 `.replace("{current_date}", ...)` 而非 `.format()` |
| 导出错题反复探测再导出（多步） | Agent 不知道应直接导出 | 确认 System Prompt "直接导出+兜底，不要先调 complex_query 探测" |
| 查看错题调了分析 Skill | "查看"和"分析"未区分 | 确认 System Prompt 区分：查看→complex_query 展示 / 分析→skill_mistake_analysis_skill |
| 子进程 GBK 编码报错 | Windows 默认编码 | 确认 `skill_adapter.py` 中 `encoding="utf-8"` + `PYTHONIOENCODING="utf-8"` |
