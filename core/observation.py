from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Observation:
    ok: bool
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    tool_name: str = ""
    source_type: str = ""
    source_name: str = ""
