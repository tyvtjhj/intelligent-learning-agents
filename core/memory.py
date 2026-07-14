import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Memory:
    messages: list[dict[str, str]] = field(default_factory=list)

    def add_system(self, content: str) -> None:
        self.messages.append({"role": "system", "content": content})

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def recent(self, limit: int = 10) -> list[dict[str, str]]:
        system_msgs = [m for m in self.messages if m["role"] == "system"]
        other_msgs = [m for m in self.messages if m["role"] != "system"]
        return system_msgs + other_msgs[-(limit - len(system_msgs)):]

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"messages": self.messages}, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, path: str | Path) -> None:
        path = Path(path)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            self.messages = data.get("messages", [])

    def snapshot(self) -> dict:
        return {"message_count": len(self.messages), "last_role": self.messages[-1]["role"] if self.messages else None}
