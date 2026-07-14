# 小宋·教育督学 Agent (EduSupervisor) — 功能总览

> 模型: DeepSeek-v4-pro | 工具总数: 27 个 | 数据库: EduSupervisor.db (13 表)

---

## 一、可用功能

| 序号 | 功能 | 触发词示例 |
|------|------|-----------|
| 1 | **费曼教学讲解** | "解释一下光合作用" "什么是牛顿第一定律" |
| 2 | **布鲁姆精熟出题** | "给我出几道化学题" "出题考考我" |
| 3 | **批量导入错题 CSV** | "导入错题" "把这个 CSV 上传题库" |
| 4 | **搜题 / 查题库** | "有没有关于勾股定理的题目" |
| 5 | **学习计划制定** | "帮我制定一个7天复习计划" |
| 6 | **错题分析** | "分析我的错题" "我哪块最薄弱" |
| 7 | **学习报告生成** | "生成学习报告" "看看我的学习情况" |
| 8 | **掌握度查询** | "我分数学得怎么样" |
| 9 | **学科 / 知识点浏览** | "有哪些学科" "小学数学有哪些知识点" |
| 10 | **联网搜索未知知识** | "什么是量子纠缠"（本地无则自动联网） |
| 11 | **学习统计与趋势** | "学习统计" "薄弱点排行" |
| 12 | **文本读写** | "帮我保存这段笔记" "读一下上次的报告" |
| 13 | **计算器** | "帮我算 125×37" |
| 14 | **教科书同步学习** | "按人教版数学八年级教"（hermes_edu 教材同步） |
| 15 | **单项能力训练** | "英语词汇每日训练" "中考冲刺"（hermes_edu 专项） |
| 16 | **自动知识入库** | 回答本地没有的问题后，自动存到本地题库 |

---

## 二、全部能力清单（Tools / Skills / MCPs）

### 🔧 本地 Tool（14个，Python 函数直接调用）

| 名称 | 中文 | 描述 |
|------|------|------|
| `calculator` | 安全计算器 | 支持 +-\*/%** 运算，基于 AST 解析 |
| `get_current_time` | 获取当前时间 | 返回日期、时间、时区、星期 |
| `save_text` | 保存文本 | 将文本写入 workspace/ 目录 |
| `read_text` | 读取文本 | 从 workspace/ 目录读取文件 |
| `list_import_files` | 列出导入文件 | 列出 imports/mistakes/ 下 CSV 错题文件 |
| `db_list_subjects` | 列出学科 | 返回 13 个学科（小学→高中+通用知识） |
| `db_list_knowledge_points` | 列出知识点 | 按学科 ID 查知识点（含层级结构） |
| `db_get_question` | 查询题目 | 按 ID 查单题完整信息 |
| `db_search_questions` | 搜索题目 | 关键词模糊匹配题目内容和知识点名 |
| `db_get_mastery_score` | 掌握度评分 | 查某知识点掌握度 (0.0-1.0) |
| `db_get_mistake_count` | 错题数量 | 查某知识点的错题数 |
| `db_get_recent_sessions` | 近期学习会话 | 最近 N 条学习记录 |
| `db_save_new_knowledge` | 保存新知识 | 一键入库知识点+题目（非题库问题自动用） |

### 📦 自建 Skill（4个，Python 子进程执行脚本）

| 名称 | 注册名 | 描述 |
|------|--------|------|
| 学习报告 Skill | `skill_learning_report_skill` | 根据学习会话生成 Markdown 学习报告 |
| 错题分析 Skill | `skill_mistake_analysis_skill` | 分析错题分布、薄弱知识点、错误类型 |
| 题目导入 Skill | `skill_question_import_skill` | 批量导入 CSV 题目，支持灵活列名+自动学科归类 |
| 学习计划 Skill | `skill_study_plan_skill` | 根据薄弱点和学科生成个性化学习计划 |

### 📥 外部 Skill（3个直接注册 + 1个 Skill Pack，内容注入模式）

| 名称 | 注册名 | 描述 |
|------|--------|------|
| 费曼教学 Skill | `external_skill_feynman_tutor` | 7条费曼纪律：生活类比、零术语、ASCII图解、深钻方向 |
| 精熟练习 Skill | `external_skill_sigma` | 布鲁姆精熟学习法出题，直到掌握为止 |
| Hermes Edu Pack | `external_skill_hermes_edu` | 170个教育 Skill 合集，分8大类 |

**Hermes Edu 8大分类：**

| 分类 | Skill 数 | 说明 |
|------|---------|------|
| textbook-sync | 26 | 教材同步（人教/苏教/北师大/外研/鲁科版） |
| daily-practice | 24 | 每日训练（口算、听写、词汇、速练） |
| exam-prep | 30 | 备考冲刺（中考/高考/四六级/教资/公务员） |
| teacher-tools | 27 | 教师工具（备课/出题/单元复习/家校沟通） |
| learning-core | 17 | 核心学习（学习计划/错题复习/记忆法/专注训练） |
| reading-writing | 10 | 阅读写作（现代文/英语写作/学术写作） |
| career-learning | 7 | 职后学习（Python/数据分析/AI/职场写作） |
| family-education | 8 | 家庭教育（亲子共读/习惯养成/情感支持） |
| language-learning | 3 | 语言考试（IELTS/TOEFL/成人语言） |

### 🔌 自建 MCP（6个，JSON-RPC 子进程通信）

| 名称 | 注册名 | 描述 |
|------|--------|------|
| 复杂 SQL 查询 | `self_mcp_complex_query` | 参数化安全 SQL 查询（读白名单表） |
| 批量插入 | `self_mcp_batch_insert` | 批量 INSERT 数据到练习/错题/掌握度表 |
| 导出查询结果 | `self_mcp_export_query` | 导出 SELECT 结果为 JSON/CSV |
| 学习统计 | `self_mcp_learning_stats` | 按学科查掌握度分布，返回雷达图数据 |
| 薄弱点排行 | `self_mcp_weak_point_ranking` | 按学科排名，薄弱知识点 Top N |
| 掌握度趋势 | `self_mcp_mastery_trend` | 按知识点查掌握度历史趋势 |

### 🌐 外部 MCP（1个，Bing 联网搜索）

| 名称 | 注册名 | 描述 |
|------|--------|------|
| 联网搜索 | `external_search` | 当本地题库无结果时联网获取知识，3次重试+双UA轮换 |

> 注：`external_mcp_config.json` 中的 `math_js` 和 `brave_search` 当前 disabled，未启用。

---

## 三、全面测试用例

> 按顺序逐个输入，每条测试语句下方标注预期会涉及的工具/Skill/MCP。
> 建议用 `clear` 命令清除上下文后开始测试。

### 第一部分：本地 Tool 测试（🔧）

| # | 测试语句 | 预期触发 |
|---|---------|---------|
| 1 | `帮我算一下 128 × 37 + 256` | 🔧 `calculator` |
| 2 | `现在几点了` | 🔧 `get_current_time` |
| 3 | `有哪些学科` | 🔧 `db_list_subjects` |
| 4 | `小学数学有哪些知识点` | 🔧 `db_list_knowledge_points` |
| 5 | `找一下和勾股定理有关的题` | 🔧 `db_search_questions` |
| 6 | `题目 1 的详细信息` | 🔧 `db_get_question` |
| 7 | `我最近学习情况怎么样` | 🔧 `db_get_recent_sessions` |
| 8 | `帮我把这段话存一下：今天学了分数加减法` | 🔧 `save_text` |
| 9 | `读取我保存的笔记` | 🔧 `read_text` |
| 10 | `导入错题` | 🔧 `list_import_files` → 显示 CSV 文件列表 |
| 11 | `知识点的掌握度怎么样` | 🔧 `db_get_mastery_score` |
| 12 | `这个知识点有多少错题` | 🔧 `db_get_mistake_count` |

### 第二部分：自建 Skill 测试（📦）

| # | 测试语句 | 预期触发 |
|---|---------|---------|
| 13 | `第一个`（承接#10选文件后）→ 选学科 → `1` | 🔧 `list_import_files` → 📦 `skill_question_import_skill` |
| 14 | `帮我制定一个 7 天复习计划` → `小学数学` | 📦 `skill_study_plan_skill` |
| 15 | `生成一份学习报告` | 📦 `skill_learning_report_skill` |
| 16 | `分析我的错题` | 📦 `skill_mistake_analysis_skill` |

### 第三部分：外部 Skill 测试（📥）

| # | 测试语句 | 预期触发 |
|---|---------|---------|
| 17 | `什么是光合作用` | 🔧 `db_search_questions` → 📥 `external_skill_feynman_tutor` |
| 18 | `给我出几道物理题考考我` | 📥 `external_skill_sigma` |
| 19 | `用三角函数公式教我` | 📥 `external_skill_hermes_edu`（注入教学方法） |

### 第四部分：自建 MCP 测试（🔌）

| # | 测试语句 | 预期触发 |
|---|---------|---------|
| 20 | `初中物理的学习统计数据` | 🔌 `self_mcp_learning_stats` |
| 21 | `我最薄弱的10个知识点是哪些` | 🔌 `self_mcp_weak_point_ranking` |
| 22 | `四则运算的掌握度变化趋势` | 🔌 `self_mcp_mastery_trend` |
| 23 | `用 SQL 查一下所有选择题` | 🔌 `self_mcp_complex_query` |
| 24 | `导出所有数学题到 CSV` | 🔌 `self_mcp_export_query` |

### 第五部分：外部 MCP 测试（🌐）

| # | 测试语句 | 预期触发 |
|---|---------|---------|
| 25 | `什么是量子场论` | 🔧 `db_search_questions`(count=0) → 🌐 `external_search` → 📥 `external_skill_feynman_tutor` → 🔧 `db_save_new_knowledge` |

### 第六部分：组合场景（综合验收）

| # | 测试语句 | 预期触发 |
|---|---------|---------|
| 26 | `导入错题` → 选文件 → 选学科 | 🔧 `list_import_files` → 📦 `skill_question_import_skill` → 返回各学科分布 |
| 27 | `status` | 验收进度：应显示 ✓ 本地Tool ✓ 自建Skill ✓ 外部Skill ✓ 自建MCP ✓ 外部MCP |

---

## 四、工具注册流程

```
agent.py 启动
  ├─ register_all_local_tools()    → 14 个 🔧 本地 Tool
  ├─ SkillAdapter.load_all()      → 4 个 📦 自建 Skill
  ├─ SkillAdapter.load_external() → 3 个 📥 外部 Skill + hermes_edu Pack
  └─ MCPAdapter.start_all()       → 6 个 🔌 自建 MCP + 0 个 🌐 外部 MCP (disabled)
                                    + 1 个 external_search (自建 Python 子进程)
─────────────────────────────────────────────────
  合计: 27 个工具
```

## 五、验收标准

启动后输入 `status` 查看验收进度，所有 27 个工具必须被成功调用才算全部通过：

```
[✓] 本地Tool调用
[✓] 自建Skill调用
[✓] 外部Skill调用
[✓] 自建MCP调用
[✓] 外部MCP调用
```
