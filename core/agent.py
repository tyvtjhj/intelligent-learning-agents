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
你是教育督学 Agent，一个帮助学生学习进步的 AI 助手。

# 核心能力
1. **讲解知识**: 用费曼教学法讲解任何知识点
2. **出题练习**: 用布鲁姆精熟学习法出题，直到学生掌握
3. **导入题目**: 帮学生批量导入 CSV 题库
4. **分析错题**: 找出薄弱知识点，分析错误原因
5. **生成报告**: 生成学习报告和个性化学习计划

# 工作原则
- 先查数据库了解情况，再给出建议
- 简单查询用 db_* 工具，复杂查询用 self_mcp_complex_query
- 教学用 external_skill_feynman_tutor
- 练习用 external_skill_sigma
- 生成报告用 skill_learning_report_skill / skill_mistake_analysis_skill
- 制定计划用 skill_study_plan_skill

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

    def run(self, task: str, max_steps: int = 15) -> dict:
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
                resp = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=1024,
                )
                content = resp.choices[0].message.content.strip()
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = content.replace("```", "").strip()

                action = json.loads(content)

                if action.get("action") == "finish":
                    return {
                        "ok": True, "answer": action["answer"],
                        "steps": _step, "trace": trace,
                        "requirements": dict(self.requirements),
                    }

                if action.get("action") == "tool_call":
                    obs = self.registry.execute(
                        action["tool_name"], action.get("arguments", {})
                    )
                    trace.append(obs)
                    self._update_requirements(obs)

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
