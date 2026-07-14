from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from core.tool_spec import ToolSpec


class MCPClientProcess:
    def __init__(self, name: str, command: list[str], cwd: Path, stderr_log: Path, db_path: str = ""):
        self.name = name
        stderr_log.parent.mkdir(parents=True, exist_ok=True)
        cmd = list(command) + ([db_path] if db_path else [])
        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=open(stderr_log, "w"),
            cwd=str(cwd),
            text=True,
            encoding="utf-8",
        )
        self._tools_cache: list[dict] | None = None

    def list_tools(self) -> list[dict]:
        if self._tools_cache is not None:
            return self._tools_cache
        req = json.dumps({"method": "tools/list", "params": {}})
        self._process.stdin.write(req + "\n")
        self._process.stdin.flush()
        line = self._process.stdout.readline()
        data = json.loads(line.strip())
        self._tools_cache = data.get("tools", [])
        return self._tools_cache

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        req = json.dumps({"method": "tools/call", "params": {"name": tool_name, "arguments": arguments}})
        self._process.stdin.write(req + "\n")
        self._process.stdin.flush()
        result = self._process.stdout.readline()
        return result.strip()

    def shutdown(self) -> None:
        try:
            self._process.terminate()
            self._process.wait(timeout=5)
        except Exception:
            self._process.kill()


class MCPAdapter:
    def __init__(self, self_mcp_dir: Path, external_config: Path, workspace: Path, db_path: str):
        self.self_mcp_dir = self_mcp_dir
        self.external_config = external_config
        self.workspace = workspace
        self.db_path = db_path
        self._clients: dict[str, MCPClientProcess] = {}
        self._specs_cache: list[ToolSpec] | None = None

    def start_all(self) -> None:
        for py_file in sorted(self.self_mcp_dir.glob("*.py")):
            name = py_file.stem
            log = self.workspace / "reports" / f"{name}.stderr.log"
            client = MCPClientProcess(
                name=name,
                command=[sys.executable, str(py_file)],
                cwd=self.self_mcp_dir.parent,
                stderr_log=log,
                db_path=self.db_path,
            )
            self._clients[name] = client

        if self.external_config.exists():
            config = json.loads(self.external_config.read_text(encoding="utf-8"))
            for server in config.get("servers", []):
                if server.get("enabled") and server.get("origin") == "node":
                    name = server["name"]
                    log = self.workspace / "reports" / f"external_{name}.stderr.log"
                    client = MCPClientProcess(
                        name=f"external_{name}",
                        command=["npx", "-y"] + server["install_cmd"].split()[2:],
                        cwd=self.self_mcp_dir.parent,
                        stderr_log=log,
                    )
                    self._clients[f"external_{name}"] = client

    def to_tool_specs(self) -> list[ToolSpec]:
        if self._specs_cache is not None:
            return self._specs_cache
        specs: list[ToolSpec] = []
        for name, client in self._clients.items():
            try:
                tools = client.list_tools()
                for tool in tools:
                    tool_name = tool["name"]
                    prefix = "external_mcp" if name.startswith("external_") else "self_mcp"
                    source_name = name

                    def _make_closure(client: MCPClientProcess, tool_name: str) -> Any:
                        def _call(**kwargs: Any) -> dict:
                            raw = client.call_tool(tool_name, kwargs)
                            try:
                                return json.loads(raw)
                            except json.JSONDecodeError:
                                return {"ok": True, "raw": raw}
                        return _call

                    spec = ToolSpec(
                        name=f"{prefix}_{tool_name}" if prefix == "external_mcp" else tool_name,
                        description=tool.get("description", f"{name}/{tool_name}"),
                        parameters={"type": "object", "properties": {}, "required": []},
                        function=_make_closure(client, tool_name),
                        source_type="mcp",
                        source_name=source_name,
                    )
                    specs.append(spec)
            except Exception as e:
                print(f"[WARN] MCP {name} tools/list 失败: {e}")
        self._specs_cache = specs
        return specs

    def shutdown_all(self) -> None:
        for client in self._clients.values():
            client.shutdown()
        self._clients.clear()
        self._specs_cache = None
