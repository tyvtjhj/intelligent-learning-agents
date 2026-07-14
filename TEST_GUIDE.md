# 小宋·教育督学 Agent 测试指南

> 使用前先运行 `python scripts/seed_data.py` 导入种子数据
> 共 32 条测试用例，覆盖 28 个全部工具

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
> 导入错题
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

---

## 第二部分：自建 Skill 测试（📦，4个）

### #13 错题导入
> 承接 #10，"导入错题"返回文件列表后：
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

### #26 导出CSV（2步完成）
```
> 导出所有数学题到 CSV，还要告诉我文件位置
```
**预期触发**：🔌 `self_mcp_export_query(sql="SELECT...WHERE sub.name LIKE '%数学%'", fmt="csv", output="math_questions")` → `outputs/math_questions.csv` → **不逐题查，不循环**

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
> 导入错题 → 选cuoti1.csv → 然后分析错题
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
| 子进程 GBK 编码报错 | Windows 默认编码 | 确认 `skill_adapter.py` 中 `encoding="utf-8"` + `PYTHONIOENCODING="utf-8"` |
