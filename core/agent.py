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
from core.memory import Memory
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
- 讲解知识时先调用 external_skill_feynman_tutor 激活费曼模式，然后立即回答
- 练习时先调用 external_skill_sigma 激活精熟模式，然后立即回答
- 生成报告用 skill_learning_report_skill / skill_mistake_analysis_skill
- 制定计划用 skill_study_plan_skill
- 当数据库找不到答案时，用 external_search 联网搜索，搜到后再回答

# 题库兜底策略（重要）
1. 学生提问后，先用 db_search_questions 查本地题库
2. 如果本地查不到结果（count=0），必须先调用 external_search 联网搜索，搜到后再用费曼法讲解
3. 不要在搜索之前就先调 external_skill_feynman_tutor！
4. 搜索返回后，调用 external_skill_feynman_tutor 激活教学风格，然后 action:finish
5. 如果有必要，用 self_mcp_batch_insert 把新知识写入知识库

# 重要规则
- 调用 external_skill_* 后，只需输出一次 action:finish 即可
- 不要在 action:finish 之后再调用任何工具
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

    def run(self, task: str, max_steps: int = 15, on_answer_chunk=None, on_tool=None) -> dict:
        self._already_injected = set()
        catalog = self.registry.catalog()
        current_date = date.today().isoformat()
        messages = [
            {"role": "system", "content": EDU_AGENT_SYSTEM_PROMPT.format(current_date=current_date)},
            {"role": "system", "content": f"# 可用工具\n\n{catalog}"},
            {"role": "user", "content": f"# 任务\n\n{task}"},
        ]
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
                            f"你现在应该输出 action:finish 直接回答用户的原始问题：{task}\n"
                            f"记住：回答中要展示费曼教学风格（生活类比、零术语、ASCII图解）。"
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
