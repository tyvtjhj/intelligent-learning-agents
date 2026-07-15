# EduSupervisor 项目结构

> 教育督学 Agent（小宋），DeepSeek-v4-pro 驱动，CLI 交互。SQLite 知识库 + 5 层能力体系。

## 启动方式

```bash
cd EduSupervisor
python agent.py
```

需要 `config.py`（gitignored）：
```python
API_KEY = "sk-xxx"
BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-v4-pro"
```

## 目录结构

```
EduSupervisor/
├── agent.py                       # 🚀 CLI入口（主循环+上下文记忆+工具标签）
├── config.py                      # 🔑 API密钥（gitignored）
├── requirements.txt               # openai
├── EduSupervisor.db               # 📦 SQLite数据库
├── CAPABILITIES.md                # 📖 功能总览+工具清单+测试用例
├── TEST_GUIDE.md                  # 🧪 测试指南
├── PROJECT_STRUCTURE.md           # 📁 本文件
│
├── core/                          # ⚙️ 核心引擎
│   ├── agent.py                   #   UnifiedAgent: ReAct多步编排+System Prompt
│   ├── memory.py                  #   Memory: 会话内多轮对话上下文（不写DB）
│   ├── llm_brain.py               #   LLMBrain: OpenAI流式调用封装
│   ├── tool_spec.py               #   ToolSpec: 统一能力描述结构
│   ├── tool_registry.py           #   ToolRegistry: 工具注册/查找/执行/目录
│   ├── observation.py             #   Observation: 工具调用结果
│   ├── safe_path.py               #   路径沙箱校验
│   └── adapters/
│       ├── skill_adapter.py       #   SkillAdapter: 本地Skill+外部Skill+Skill Pack加载
│       └── mcp_adapter.py         #   MCPAdapter: MCP服务器进程管理+工具注册
│
├── db/                            # 🗄️ 数据库
│   ├── schema.sql                 #   13张表（subjects/knowledge_points/questions/question_tags/
│   │                              #          study_sessions/practice_records/mistake_log/
│   │                              #          mastery_scores/study_reports/conversation_messages/
│   │                              #          general_knowledge）
│   └── connection.py              #   SQLite单例+WAL模式
│
├── tools/                         # 🔧 本地工具（Python函数）
│   ├── utility_tools.py           #   calculator/get_current_time/save_text/read_text(list)/list_import_files
│   ├── db_tools.py                #   db_list_subjects/list_kp/get_question/search_questions/
│   │                              #   get_mastery/get_mistake/get_recent_sessions/
│   │                              #   save_new_knowledge/save_conversation/load_conversation
│   └── local_tools.py             #   工具注册入口：register_all_local_tools()
│
├── skills/                        # 📦 自建 Skill（SKILL.md + scripts/runner.py）
│   ├── learning_report_skill/     #   学习报告生成
│   ├── mistake_analysis_skill/    #   错题分析
│   ├── question_import_skill/     #   批量导入CSV题目（支持灵活列名+自动学科归类）
│   └── study_plan_skill/          #   个性化学习计划生成
│
├── installed_external_skills/     # 📥 外部 Skill
│   ├── feynman_tutor/             #   费曼式深度教学（7条纪律：类比/术语/ASCII图解/...）
│   ├── sigma/                     #   布鲁姆精熟学习出题模式
│   └── hermes_edu/                #   170个教育Skill Pack（catalog.json）:
│                                   #   textbook-sync/daily-practice/exam-prep/reading-writing/
│                                   #   teacher-tools/learning-core/career-learning/...
│
├── mcp_servers/                   # 🔌 自建 MCP（stdio JSON-RPC）
│   ├── sqlite_mcp_server.py       #   复杂SQL查询+批量插入+导出CSV文件
│   ├── analysis_mcp_server.py     #   数据分析+统计+时间趋势
│   └── web_search_mcp_server.py   #   🌐 Bing联网搜索（3次重试+双UA轮换）
│
├── external_mcp/                  # 🌐 外部 MCP
│   └── external_mcp_config.json   #  外部MCP服务器配置（当前全部disabled）
│
├── imports/                       # 📥 学生数据导入
│   ├── TEMPLATE_mistakes.csv      #   错题CSV模板
│   └── mistakes/                  #   学生CSV题库文件（gitignored）
│
├── outputs/                       # 📤 导出文件目录（CSV/报告等，gitignored）
│   └── .gitkeep
│
├── workspace/                     # 📝 工作目录（笔记/临时文件，gitignored）
│   ├── reports/                   #   技能/报告输出
│   ├── processed/
│   └── exports/
│
└── scripts/                       # 🛠️ 工具脚本
    ├── init_db.py                 #   数据库初始化（建表）
    ├── seed_data.py               #   种子数据（13学科×知识点×题目）
    ├── validate_skills.py         #   Skill安全审查
    └── install_external_skills.py #   外部Skill安装
```

## 架构分层

```
┌─────────────────────────────────────┐
│  5️⃣ Agent编排层 (agent.py CLI)      │  多轮对话 / 上下文记忆 / 流式输出
├─────────────────────────────────────┤
│  4️⃣ 能力适配层 (adapters/)          │  Skill → ToolSpec / MCP → ToolSpec
├─────────────────────────────────────┤
│  3️⃣ 能力实现层 (tools/skills/mcp)   │  14本地Tool + 4自建Skill + 3外部Skill + 7MCP
├─────────────────────────────────────┤
│  2️⃣ 模型通信层 (llm_brain)          │  OpenAI stream=True / 流式JSON解析
├─────────────────────────────────────┤
│  1️⃣ 基础设施层 (db/)                │  SQLite WAL / 单例连接 / 路径沙箱
└─────────────────────────────────────┘
```

## 统一抽象：ToolSpec → Observation

```
ToolSpec                 →  execute  →  Observation
├── name, description    →           ├── ok, error
├── parameters (JSON Schema)         ├── result (dict)
├── function/source_type             ├── tool_name
└── source_name(mcp/skill/function)  └── source_type
```

## 能力分类（共 28 个工具，启动时全部注册）

| 类型 | 标签 | 数量 | 示例 |
|------|------|------|------|
| 🔧 本地 Tool | function | 14 | `db_search_questions`, `read_text`, `list_import_files` |
| 📦 自建 Skill | skill | 4 | `skill_study_plan_skill`, `skill_question_import_skill` |
| 📥 外部 Skill | skill | 3 | `external_skill_feynman_tutor`, `external_skill_sigma`, `external_skill_hermes_edu` |
| 🔌 自建 MCP | mcp | 6 | `self_mcp_complex_query`, `self_mcp_export_query`, `self_mcp_learning_stats` |
| 🌐 外部 MCP | mcp | 1 | `external_search`（Bing联网，自建Python子进程） |

## 核心工作流

### 题库兜底：本地命中 → 直接讲解
```
学生提问 → db_search_questions(count>0)
        → external_skill_feynman_tutor(激活费曼模式)
        → action:finish(费曼风格回答)
        → ⚠️ 不重复入库
```

### 题库兜底：本地未命中 → 联网搜索 → 自动入库
```
学生提问 → db_search_questions(count=0)
        → external_search(3次重试)
        → external_skill_feynman_tutor(激活费曼模式)
        → db_list_subjects(查学科ID)
        → db_save_new_knowledge(📥自动入库)
        → action:finish(费曼风格回答)
```

### 题库导入：自动学科归类
```
学生说"导入题库" → list_import_files(列出CSV)
               → skill_question_import_skill(csv_path="...", 不传subject_id=自动归类)
               → 知识点关键词→学科映射（加法→小学数学, 唐诗→初中语文, 天文→通用知识）
               → 返回各学科分布
```

### 数据导出：2步完成
```
学生说"导出XX到CSV" → self_mcp_export_query(sql="...", fmt="csv", output="文件名")
                   → 文件写入 outputs/xxx.csv
                   → action:finish 告知路径
```

### 读取笔记：列文件→读文件
```
学生说"读取笔记" → read_text(不传filename) → 列出workspace/下所有文件
               → 学生选文件 → read_text(filename="xxx") → 直接展示内容
```

### 输出格式（JSON Action）
```
{"action":"tool_call","tool_name":"<名>","arguments":{<参数>},"reason":"<原因>"}
{"action":"finish","answer":"<回复>"}
```

## 关键数据库表

| 表 | 用途 |
|----|------|
| `subjects` | 学科（13个：小学数学→高中生物+通用知识） |
| `knowledge_points` | 知识点（3级层级，含difficulty） |
| `questions` | 题目（5种类型，含source追踪csv_import/manual） |
| `question_tags` | 题目标签 |
| `mastery_scores` | 掌握度评分（0-1，支持间隔复习） |
| `mistake_log` | 错题记录（含error_type+resolved） |
| `study_sessions` | 学习会话 |
| `practice_records` | 练习记录 |
| `study_reports` | 学习报告元数据（content_path指向workspace/reports/） |
| `conversation_messages` | 对话持久化（session_id+seq，当前不启用） |
| `general_knowledge` | 🆕 通用知识点（跨学科常识, 信息技术等） |

## 安全机制

- Skill 审查：8种危险模式检测（subprocess/socket/requests/os.system/exec/eval/__import__/shutil.rmtree）
- MCP 隔离：独立 stdio 子进程，encoding="utf-8", PYTHONIOENCODING="utf-8"
- 路径沙箱：`safe_path.py` 限制文件读写范围
- SQL 注入防护：MCP 查询使用参数化SQL+白名单表+DROP/DELETE/UPDATE/ALTER禁止
- 外部Skill注入模式：不执行代码，仅注入SKILL.md内容到System Prompt
- API Key 隔离：`config.py` 已 gitignore，历史commit无泄露

## CLI 命令

| 命令 | 作用 |
|------|------|
| `quit` | 退出 |
| `status` | 查看5层能力验收进度 |
| `clear` | 清除当前对话上下文（内存中Memory重置） |
