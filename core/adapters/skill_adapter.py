from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from dataclasses import dataclass

from core.tool_spec import ToolSpec


DANGEROUS_PATTERNS = [
    (r"\bsubprocess\b", "子进程调用"),
    (r"\bsocket\b", "网络连接"),
    (r"\brequests\.(get|post|put|delete|patch)\b", "HTTP 请求"),
    (r"\bos\.system\b", "系统命令执行"),
    (r"\bexec\s*\(", "动态代码执行"),
    (r"\beval\s*\(", "动态表达式求值"),
    (r"\b__import__\s*\(", "动态导入"),
    (r"\bshutil\.rmtree\b", "递归删除目录"),
]


@dataclass
class SkillSpec:
    name: str
    description: str
    when_to_use: str
    inputs: dict[str, Any]
    safety: str
    script_path: Path
    skill_dir: Path


class SkillAdapter:
    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir
        self.external_specs: list[ToolSpec] = []

    def load_all(self) -> list[ToolSpec]:
        specs: list[ToolSpec] = []
        if not self.skills_dir.exists():
            return specs

        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                try:
                    spec = self._load_skill_dir(skill_dir)
                    if spec:
                        specs.append(spec)
                except Exception as e:
                    print(f"[WARN] 加载 Skill 失败: {skill_dir.name}, {e}")
        return specs

    def _load_skill_dir(self, skill_dir: Path) -> ToolSpec | None:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            return None

        runner = skill_dir / "scripts" / "runner.py"
        if not runner.exists():
            return None

        parsed = self._parse_skill_md(skill_md.read_text(encoding="utf-8"), skill_dir, runner)

        def _skill_closure(**kwargs: Any) -> dict:
            workspace = self.skills_dir.parent / "workspace"
            cmd = [sys.executable, str(runner), json.dumps(kwargs), str(workspace)]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode != 0:
                    return {"ok": False, "error": result.stderr.strip() or result.stdout.strip()}
                return json.loads(result.stdout.strip())
            except subprocess.TimeoutExpired:
                return {"ok": False, "error": "Skill 执行超时 (120s)"}
            except Exception as e:
                return {"ok": False, "error": str(e)}

        return ToolSpec(
            name=f"skill_{skill_dir.name}",
            description=parsed["description"],
            parameters=parsed["parameters"],
            function=_skill_closure,
            source_type="skill",
            source_name=skill_dir.name,
        )

    def _parse_skill_md(self, content: str, skill_dir: Path, runner: Path) -> dict:
        desc = ""
        params: dict[str, Any] = {"type": "object", "properties": {}, "required": []}

        name_match = re.search(r"#\s+(.+)", content)
        name = name_match.group(1).strip() if name_match else skill_dir.name

        desc_match = re.search(r"##\s+功能概述\s*\n\s*(.+?)(?:\n##|\Z)", content, re.DOTALL)
        if desc_match:
            desc = desc_match.group(1).strip()

        param_section = re.search(r"##\s+输入参数\s*\n(.*?)(?:\n##|\Z)", content, re.DOTALL)
        if param_section:
            for line in param_section.group(1).strip().split("\n"):
                line = line.strip()
                if line.startswith("|") and not line.startswith("|--"):
                    parts = [p.strip() for p in line.split("|")[1:-1]]
                    if len(parts) >= 4:
                        pname, ptype, required, pdesc = parts[0], parts[1], parts[2], parts[3]
                        if pname and pname not in ("参数名", "---"):
                            params["properties"][pname] = {
                                "type": {"string": "string", "integer": "integer", "boolean": "boolean", "number": "number"}.get(ptype, "string"),
                                "description": pdesc,
                            }
                            if required.lower() == "是":
                                params["required"].append(pname)

        desc_full = f"{name}\n\n{desc}\n\n适用场景：见 SKILL.md 中的触发词。"
        return {"description": desc_full, "parameters": params}

    def load_external_skills(self, external_dir: Path) -> None:
        if not external_dir.exists():
            return
        for skill_dir in external_dir.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if not skill_md.exists():
                    continue
                try:
                    content = skill_md.read_text(encoding="utf-8")
                    self._audit_external_skill(skill_dir.name, content)
                    spec = self._make_external_spec(skill_dir.name, content)
                    if spec:
                        self.external_specs.append(spec)
                except PermissionError as e:
                    print(f"[SECURITY] 外部 Skill 审查未通过: {skill_dir.name}, {e}")

    def _audit_external_skill(self, name: str, content: str) -> None:
        issues = []
        for pattern, label in DANGEROUS_PATTERNS:
            if re.search(pattern, content):
                issues.append(f"检测到危险模式 [{label}]: {pattern}")
        if issues:
            raise PermissionError(f"外部 Skill '{name}' 安全审查未通过:\n" + "\n".join(issues))

    def _make_external_spec(self, skill_name: str, content: str) -> ToolSpec | None:
        def _external_closure(**kwargs: Any) -> dict:
            return {
                "ok": True,
                "mode": "external_skill_injection",
                "skill_name": skill_name,
                "skill_content": content[:2000],
                "context": kwargs,
            }

        return ToolSpec(
            name=f"external_skill_{skill_name}",
            description=f"外部 Skill: {skill_name}\n\n{content[:300]}...",
            parameters={"type": "object", "properties": {}, "required": []},
            function=_external_closure,
            source_type="skill",
            source_name=f"external_{skill_name}",
        )
