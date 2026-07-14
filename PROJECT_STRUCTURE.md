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
├── agent.py                       # 🚀 CLI入口（主循环+历史上下文+工具标签）
├── config.py                      # 🔑 API密钥（gitignored）
├── requirements.txt               # openai
├── EduSupervisor.db               # 📦 SQLite数据库
│
├── core/                          # ⚙️ 核心引擎
│   ├── agent.py                   #   UnifiedAgent: ReAct多步编排+System Prompt
│   ├── memory.py                  #   Memory: 对话历史积累+save_to_db/load_from_db
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
│   ├── schema.sql                 #   12张表（subjects/knowledge_points/questions/.../
│   │                              #          study_sessions/mistake_log/mastery_scores/
│   │                              #          conversation_messages/study_reports）
│   └── connection.py              #   SQLite单例+WAL模式
│
├── tools/                         # 🔧 本地工具（Python函数）
│   ├── utility_tools.py           #   calculator/get_current_time/save_text/read_text
│   ├── db_tools.py                #   db_list_subjects/list_kp/get_question/search_questions/
│   │                              #   get_mastery/get_mistake/get_recent_sessions/
│   │                              #   save_new_knowledge/save_conversation/load_conversation
│   └── local_tools.py             #   工具注册入口：register_all_local_tools()
│
├── skills/                        # 📦 自建 Skill（SKILL.md + scripts/runner.py）
│   ├── learning_report_skill/     #   学习报告生成
│   ├── mistake_analysis_skill/    #   错题分析
│   ├── question_import_skill/     #   批量导入CSV题目
│   └── study_plan_skill/          #   个性化学习计划生成
│
├── installed_external_skills/     # 📥 外部 Skill
│   ├── feynman_tutor/             #   费曼式深度教学（7条纪律：类比/术语/ASCII图解/...）
│   ├── sigma/                     #   布鲁姆精熟学习出题模式
│   └── hermes_edu/                #   170个教育Skill Pack（catalog.json）:
│                                   #   textbook-sync/day-practice/exam-prep/reading-writing/
│                                   #   teacher-tools/learning-core/career-learning/...
│
├── mcp_servers/                   # 🔌 自建 MCP（stdio JSON-RPC）
│   ├── sqlite_mcp_server.py       #   复杂SQL查询+批量插入
│   ├── analysis_mcp_server.py     #   数据分析+统计+时间趋势
│   └── web_search_mcp_server.py   #   🌐 Bing联网搜索（3次重试+双UA轮换）
│
├── external_mcp/                  # 🌐 外部 MCP
│   └── external_mcp_config.json  #    外部MCP服务器配置
│
└── scripts/                       # 🛠️ 工具脚本
    ├── init_db.py                 #   数据库初始化（建表）
    ├── seed_data.py               #   种子数据（12学科×68知识点×40题目）
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
│  3️⃣ 能力实现层 (tools/skills/mcp)   │  12本地Tool + 4自建Skill + 173外部Skill + 6MCP
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

## 能力分类（共 19+ 工具，启动时全部注册）

| 类型 | 标签 | 示例 |
|------|------|------|
| 🔧 本地Tool | function | `db_search_questions`, `db_save_new_knowledge`, `calculator` |
| 📦 自建Skill | skill | `skill_study_plan_skill`, `skill_learning_report_skill` |
| 📥 外部Skill | skill | `external_skill_feynman_tutor`, `external_skill_sigma`, `external_skill_hermes_edu` |
| 🔌 自建MCP | mcp | `self_mcp_complex_query`, `self_mcp_analyze`, `self_mcp_batch_insert` |
| 🌐 外部MCP | mcp | `external_search`(Bing), `external_mcp_*` |

## 核心工作流

### 非题库问题 → 自动联网入库
```
学生提问 → db_search_questions(count=0)
        → external_search(3次重试)
        → external_skill_feynman_tutor(激活费曼模式)
        → db_save_new_knowledge(📥自动入库)
        → action:finish(费曼风格回答)
```

### 多轮对话上下文
```
启动 → load_from_db(恢复上次对话) → 显示最近4条
每轮 → history=memory.messages → agent.run()
      → memory.add_user/add_assistant
quit/Ctrl+C → memory.save_to_db(自动保存)
```

### 输出格式（JSON Action）
```
{"action":"tool_call","tool_name":"<名>","arguments":{<参数>},"reason":"<原因>"}
{"action":"finish","answer":"<回复>"}
```

## 关键数据库表

| 表 | 用途 |
|----|------|
| `subjects` | 学科(12个：小学数学→高中数学) |
| `knowledge_points` | 知识点(3级层级，含difficulty) |
| `questions` | 题目(5种类型，含source追踪) |
| `mastery_scores` | 掌握度评分(0-1，支持间隔复习) |
| `mistake_log` | 错题记录(含error_type+resolved) |
| `study_sessions` | 学习会话 |
| `conversation_messages` | 💾 **多轮对话持久化**（session_id+seq） |

## 安全机制

- Skill 审查：8种危险模式检测（subprocess/socket/requests/os.system/exec/eval/__import__/shutil.rmtree）
- MCP 隔离：独立 stdio 子进程
- 路径沙箱：`safe_path.py` 限制文件读写范围
- SQL 注入防护：MCP 查询使用参数化SQL+白名单校验
- 外部Skill注入模式：不执行代码，仅注入SKILL.md内容到System Prompt

## CLI 命令

| 命令 | 作用 |
|------|------|
| `quit` | 退出（💾自动保存对话到DB） |
| `status` | 查看5层能力验收进度 |
| `clear` | 清除当前对话上下文（不删DB记录） |
