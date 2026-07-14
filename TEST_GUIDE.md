# 小宋·教育督学 Agent 测试指南

> 使用前先运行 `python scripts/seed_data.py` 导入种子数据

---

## 启动 Agent

```bash
cd EduSupervisor
python agent.py
```

```
============================================================
  小宋·教育督学 Agent (EduSupervisor) v1.0
  模型: deepseek-v4-pro | 工具: 24 个
  输入 'quit' 退出 | 'status' 验收进度
============================================================
```

---

## 场景 1：自我介绍

```
> 你是谁？
```

**预期**：小宋自我介绍，用"我是小宋"开头，提到教育督学身份。

**覆盖知识点**：无（基础对话）

---

## 场景 2：知识点讲解（本地Tool + 外部Skill）

```
> 帮我理解什么是绝对值
```

**预期**：
- 调用 `db_list_subjects` 或直接调用 `external_skill_feynman_tutor`
- 用生活类比讲解（如"距离"）
- 回复口语化、有温度

**验收**：`本地Tool调用` ✓，`外部Skill调用` ✓

---

## 场景 3：查看学科列表（本地Tool）

```
> 有哪些可以学的学科？
```

**预期**：调用 `db_list_subjects`，返回初中数学、初中物理。

**验收**：`本地Tool调用` ✓

---

## 场景 4：查看知识点（本地Tool）

```
> 初中数学有哪些知识点？
```

**预期**：调用 `db_list_knowledge_points`，列出有理数、一元一次方程等 7 个知识点。

**验收**：`本地Tool调用` ✓

---

## 场景 5：搜索题目（本地Tool）

```
> 搜一下和方程有关的题目
```

**预期**：调用 `db_search_questions` 或 `self_mcp_complex_query`，返回一元一次方程相关题目。

**验收**：`本地Tool调用` ✓

---

## 场景 6：获取具体题目（本地Tool）

```
> 让我看看第 3 题的内容
```

**预期**：调用 `db_get_question(question_id=3)`，返回"下列哪个是一元一次方程？"及选项。

**验收**：`本地Tool调用` ✓

---

## 场景 7：计算器验证（本地Tool）

```
> 帮我算一下 (100+200)*3/5 等于多少
```

**预期**：调用 `calculator`，返回 180。

**验收**：`本地Tool调用` ✓

---

## 场景 8：生成学习报告（自建Skill + 自建MCP）

```
> 生成学习报告
```

**预期**：
- 调用 `self_mcp_learning_stats` 获取统计数据
- 调用 `skill_learning_report_skill` 生成报告
- 报告生成在 `workspace/reports/` 目录下

**验收**：`自建Skill调用` ✓，`自建MCP调用` ✓

---

## 场景 9：错题分析（自建Skill + 自建MCP）

```
> 分析错题
```

**预期**：
- 调用 `self_mcp_complex_query` 查询错题数据
- 调用 `skill_mistake_analysis_skill` 生成分析报告
- 报告列出薄弱知识点排名

**验收**：`自建Skill调用` ✓，`自建MCP调用` ✓

---

## 场景 10：制定学习计划（自建Skill + 自建MCP）

```
> 制定一个 7 天的学习计划
```

**预期**：
- 调用 `self_mcp_weak_point_ranking` 获取薄弱点
- 调用 `skill_study_plan_skill` 生成计划
- 计划含每天要复习的知识点

**验收**：`自建Skill调用` ✓，`自建MCP调用` ✓

---

## 场景 11：综合测试（尽量多知识点）

```
> 先列出数学知识点，找出我最薄弱的地方，帮我用费曼法讲解，再生成学习计划
```

**预期**：
- `db_list_knowledge_points`（本地Tool）
- `self_mcp_weak_point_ranking`（自建MCP）
- `external_skill_feynman_tutor`（外部Skill）
- `skill_study_plan_skill`（自建Skill）

**验收**：`本地Tool` ✓，`自建MCP` ✓，`外部Skill` ✓，`自建Skill` ✓

---

## 场景 12：文件读写（本地Tool）

```
> 帮我把"今天学了一元一次方程"保存为 notes.txt
```

**预期**：调用 `save_text`，文件落盘到 `workspace/notes.txt`。

```
> 读一下 notes.txt 的内容
```

**预期**：调用 `read_text`，返回刚才保存的内容。

---

## 场景 13：查看验收进度

```
> status
```

**预期**：显示 5 项验收条件的当前状态。

```
# 验收进度
[✓] 本地Tool调用
[✓] 自建Skill调用
[✓] 外部Skill调用
[✗] 自建MCP调用
[✗] 外部MCP调用
```

---

## 快速覆盖所有知识点的最小测试集

按顺序执行下面 4 句，即可覆盖全部 5 大知识点（外部 MCP 除外）：

```
> 有哪些学科？
> 帮我理解什么是绝对值
> 生成学习报告
> 分析错题
```

| 知识点 | 触发场景 | 验收 |
|--------|---------|------|
| 本地 Tool | 场景 2-7（db_*, calculator 等） | `db_list_subjects` 被调用 |
| 自建 Skill | 场景 8-10（learning_report, mistake_analysis, study_plan） | 报告文件生成 |
| 外部 Skill | 场景 2, 11（feynman/sigma/hermes） | `external_skill_*` 被调用 |
| 自建 MCP | 场景 8-10（complex_query, learning_stats 等） | `self_mcp_*` 被调用 |
| 外部 MCP | 外部 MCP 默认关闭，需先在 `external_mcp_config.json` 中设置 `enabled: true` | `external_mcp_*` 被调用 |

---

## 常见问题排查

| 现象 | 可能原因 | 解决 |
|------|---------|------|
| Agent 回答卡住不动 | API 超时或上下文过长 | Ctrl+C 重新运行 |
| 工具未找到 | 种子数据未导入 | 运行 `python scripts/seed_data.py` |
| 外部 Skill 加载失败 | 未安装外部仓库 | 运行 `python scripts/install_external_skills.py` |
| 流式输出不显示 | DeepSeek 流式支持 | 等待3-5秒，无需处理 |
