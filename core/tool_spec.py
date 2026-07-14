from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    function: Callable[..., Any]
    source_type: str = "function"
    source_name: str = "local"
