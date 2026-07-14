import json
import sys
from pathlib import Path
from datetime import date
from collections import OrderedDict
from dataclasses import dataclass, field

from openai import OpenAI

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.tool_registry import ToolRegistry
from core.observation import Observation

EDU_AGENT_SYSTEM_PROMPT = """\
# 角色
你的名字叫"小宋"，是教育督学 Agent，一个帮助学生学习进步的 AI 助手。

# 核心能力
1. **讲解知识**: 用费曼教学法讲解任何知识点
2. **出题练习**: 用布鲁姆精熟学习法出题，直到学生掌握
3. **导入题目**: 帮学生批量导入 CSV 题库
4. **分析错题**: 找出薄弱知识点，分析错误原因
5. **生成报告**: 生成学习报告和个性化学习计划

# 费曼教学法（讲解时默认使用）
1. 先说生活类比和画面，再回到术语
2. 零术语裸奔：英文缩写首次出现必须给全称+翻译+大白话
3. 用 ASCII 图把复杂机制画出来
4. 默认零基础起步，但稍微超前一点点
5. 最后给 3-4 个深钻方向

# 工作原则
- 先查数据库了解情况，再给出建议
- 简单查询用 db_* 工具，复杂查询用 self_mcp_complex_query
- **讲解任何知识点或概念时，必须先调用 external_skill_feynman_tutor 激活费曼教学模式，然后立即回答**
- 练习时先调用 external_skill_sigma 激活精熟模式，然后立即回答
- **学生要求制定学习计划（如"7天计划""复习计划"）时，必须调用 skill_study_plan_skill 生成计划，不要只查学科就提问**
- 生成报告用 skill_learning_report_skill / skill_mistake_analysis_skill
- 当数据库找不到答案时，用 external_search 联网搜索，搜到后再回答
- **学生说"用XX方法/思路/框架教我"时，调用 external_skill_hermes_edu 注入对应教学法**
- **读取笔记/文件时：先调 read_text(不传filename) 列文件列表，再调 read_text(filename="xxx") 读具体文件，不要额外查数据库**
- **所有生成的文件（导出CSV、报告、笔记等）统一放到 outputs/ 目录**

# 数据导出（重要！最多2步完成）
1. 学生要求"导出XX到CSV"时 → 调用 **self_mcp_export_query**
   - SQL 示例: SELECT q.content, q.answer, q.question_type, kp.name AS knowledge_point, sub.name AS subject FROM questions q JOIN knowledge_points kp ON q.kp_id = kp.id JOIN subjects sub ON kp.subject_id = sub.id WHERE sub.name LIKE '%数学%'
   - 参数: sql="上面的SQL", fmt="csv", output="math_questions"
2. 导出成功 → action:finish 告知文件路径："文件已导出到 outputs/xxx.csv"
3. ⚠️ **不要导出了还继续用 db_get_question 逐题查！一次 self_mcp_export_query 就够了！**

# 题库导入（重要！严格按这个流程）
1. 学生说"导入错题"→ 立即调用 **list_import_files** 列出 imports/mistakes/ 下的 CSV 文件
2. 把文件列表展示给学生，让用户选一个或多个文件
3. 用户选定后 → 调用 **skill_question_import_skill**，参数: csv_path="imports/mistakes/xxx.csv"
   - ⚠️ skill_question_import_skill 的参数名是 **csv_path**（不是 path/file/filename）
   - **subject_id 是可选的，不传则根据知识点名称自动分类到对应学科（加法→小学数学，唐诗→初中语文，天文→通用知识等）**
   - 如果想让学生手动指定学科，先调 db_list_subjects 让学生选
4. 导入结果返回后 action:finish 告知学生导入成功和各学科分布

# 题库兜底策略（重要！严格按条件分支）
1. 学生提问后，先用 db_search_questions 查本地题库
2. **分支A - 本地命中（count > 0）**：
   a. 直接调用 external_skill_feynman_tutor 激活费曼教学
   b. action:finish 用费曼风格回答，基于 db_search_questions 返回的内容
   c. ⚠️ 本地已有就不要调 db_save_new_knowledge 重复入库！不要查 db_list_subjects！
3. **分支B - 本地未命中（count = 0）**：
   a. 调用 external_search 联网搜索（3次重试）
   b. 搜索返回后，调用 external_skill_feynman_tutor 激活教学风格
   c. 调用 db_list_subjects 查对应学科ID
   d. 调用 db_save_new_knowledge 把新知识点+题目入库
   e. action:finish 用费曼风格回答
4. 如果 external_search 也失败了（retry_exhausted=true），用自己的知识回答，同样走 3c→3d→3e 入库
5. 不要在搜索之前就先调 external_skill_feynman_tutor！

# 重要规则
- 调用 external_skill_* 后，只需输出一次 action:finish 即可
- 不要在 action:finish 之后再调用任何工具
- ⚠️ **db_save_new_knowledge 只在 db_search_questions 返回 count=0 时才调用**，本地已命中的知识点不要重复入库
- 调用 db_save_new_knowledge 前先通过 db_list_subjects 确认正确的 subject_id
- 回答要口语化、有温度，像真人老师

# 输出格式
你只能输出 JSON:
{{"action":"tool_call","tool_name":"<工具名>","arguments":{{<参数>}},"reason":"<原因>"}}
{{"action":"finish","answer":"<回复>"}}

# 当前日期
{current_date}
"""


@dataclass
class UnifiedAgent:
    client: OpenAI
    model_name: str
    registry: ToolRegistry
    requirements: OrderedDict

    def run(self, task: str, max_steps: int = 15, on_answer_chunk=None, on_tool=None, history: list[dict[str, str]] | None = None) -> dict:
        self._already_injected = set()
        catalog = self.registry.catalog()
        current_date = date.today().isoformat()
        messages = [
            {"role": "system", "content": EDU_AGENT_SYSTEM_PROMPT.format(current_date=current_date)},
            {"role": "system", "content": f"# 可用工具\n\n{catalog}"},
        ]
        if history:
            recent_history = history[-20:]
            messages.append({"role": "system", "content": (
                "# 对话历史\n以下是之前的对话记录，请结合上下文理解用户当前输入（如'1''对''继续'等简略回复）。"
            )})
            messages.extend(recent_history)
        messages.append({"role": "user", "content": f"# 任务\n\n{task}"})
        trace: list[Observation] = []

        for _step in range(1, max_steps + 1):
            try:
                content = self._stream_collect(messages, on_answer_chunk)

                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = content.replace("```", "").strip()

                action = json.loads(content)
                act = action.get("action", "")

                if act == "finish":
                    self._stream_answer(action.get("answer", ""), on_answer_chunk)
                    return {
                        "ok": True, "answer": action["answer"],
                        "steps": _step, "trace": trace,
                        "requirements": dict(self.requirements),
                    }

                if act == "tool_call":
                    spec = self.registry.get(action["tool_name"])
                    source_type = spec.source_type if spec else "unknown"
                    source_name = spec.source_name if spec else ""
                    if on_tool:
                        on_tool(action["tool_name"], action.get("reason", ""), source_type, source_name)
                    obs = self.registry.execute(
                        action["tool_name"], action.get("arguments", {})
                    )
                    trace.append(obs)
                    self._update_requirements(obs)

                    if obs.ok and obs.result.get("mode") == "external_skill_injection":
                        skill_name = obs.tool_name
                        messages.append({"role": "assistant", "content": content})
                        self._already_injected.add(action["tool_name"])
                        messages.append({"role": "user", "content": (
                            f"{skill_name} 模式已激活，教学风格已切换。\n"
                            f"请按顺序操作：\n"
                            f"1. 先调用 db_save_new_knowledge 将新知识点和题目存入本地数据库（用 db_list_subjects 找到对应学科ID）\n"
                            f"2. 然后 action:finish 用费曼风格回答用户的原始问题：{task}\n"
                            f"记住：回答中要展示费曼教学风格（生活类比、零术语、ASCII图解）。\n"
                            f"注意：千万不要跳过第1步，必须先把知识入库！"
                        )})
                        continue

                    if obs.ok and obs.result.get("mode") == "external_skill_pack":
                        messages.append({"role": "assistant", "content": content})
                        messages.append({"role": "user", "content": "请直接回答用户问题。"})
                        continue

                    if obs.ok and action["tool_name"].startswith("skill_"):
                        result_str = json.dumps(obs.result, ensure_ascii=False)[:2000]
                        messages.append({"role": "assistant", "content": content})
                        messages.append({"role": "user", "content": (
                            f"Skill 执行结果: {result_str}\n\n"
                            "不要再用 read_text 去读文件。直接 action:finish，"
                            "把结果中的内容用自然语言讲给学生。"
                        )})
                        continue

                    if obs.ok:
                        result_str = json.dumps(obs.result, ensure_ascii=False)[:2000]
                        messages.append({"role": "assistant", "content": content})
                        messages.append({"role": "user", "content": f"执行结果: {result_str}"})
                    else:
                        messages.append({"role": "assistant", "content": content})
                        messages.append({"role": "user", "content": f"失败: {obs.error}"})

            except json.JSONDecodeError:
                messages.append({"role": "user", "content": "请输出有效 JSON"})
            except Exception as e:
                messages.append({"role": "user", "content": f"错误: {e}"})

        return {
            "ok": False, "answer": "达到最大步数",
            "steps": max_steps, "trace": trace,
            "requirements": dict(self.requirements),
        }

    def _stream_collect(self, messages, on_chunk) -> str:
        buffer = ""
        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            buffer += delta
        return buffer

    def _stream_answer(self, answer: str, on_chunk) -> None:
        if on_chunk:
            on_chunk(answer)

    def _requirements_status(self) -> str:
        lines = ["# 验收进度"]
        for cond, status in self.requirements.items():
            lines.append(f"[{'✓' if status else '✗'}] {cond}")
        return "\n".join(lines)

    def _update_requirements(self, obs: Observation) -> None:
        name = obs.tool_name
        source = obs.source_type

        if source == "function" and obs.ok:
            self.requirements["本地Tool调用"] = True

        if source == "skill" and name.startswith("skill_") and obs.ok:
            self.requirements["自建Skill调用"] = True

        if source == "skill" and name.startswith("external_skill_") and obs.ok:
            self.requirements["外部Skill调用"] = True

        if source == "mcp" and name.startswith("self_mcp_") and obs.ok:
            self.requirements["自建MCP调用"] = True

        if source == "mcp" and name.startswith("external_mcp_") and obs.ok:
            self.requirements["外部MCP调用"] = True
