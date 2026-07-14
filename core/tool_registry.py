from __future__ import annotations

from typing import Any
from core.tool_spec import ToolSpec
from core.observation import Observation


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def catalog(self) -> str:
        lines = []
        for name, spec in self._tools.items():
            lines.append(f"### {name} ({spec.source_type})")
            lines.append(f"{spec.description}")
            lines.append("")
        return "\n".join(lines).strip()

    def count(self) -> int:
        return len(self._tools)

    def execute(self, name: str, arguments: dict[str, Any]) -> Observation:
        spec = self._tools.get(name)
        if spec is None:
            return Observation(
                ok=False,
                error=f"工具 {name} 未注册",
                tool_name=name,
                source_type="unknown",
            )
        try:
            result = spec.function(**arguments)
            if isinstance(result, dict) and "ok" in result:
                ok = result["ok"]
            else:
                ok = True
            return Observation(
                ok=ok,
                result=result if isinstance(result, dict) else {"value": result},
                tool_name=name,
                source_type=spec.source_type,
                source_name=spec.source_name,
            )
        except Exception as e:
            return Observation(
                ok=False,
                error=str(e),
                tool_name=name,
                source_type=spec.source_type,
                source_name=spec.source_name,
            )
