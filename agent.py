import sys
from pathlib import Path
from collections import OrderedDict
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent))

from config import API_KEY, BASE_URL, MODEL_NAME
from core.tool_registry import ToolRegistry
from core.agent import UnifiedAgent
from core.memory import Memory
from core.adapters.skill_adapter import SkillAdapter
from core.adapters.mcp_adapter import MCPAdapter
from tools.local_tools import register_all_local_tools
from db.connection import set_db_path


def _tool_label(name: str, source_type: str, source_name: str) -> tuple[str, str]:
    """返回 (中文标签, emoji图标)"""
    if source_type == "mcp":
        if source_name.startswith("external_") or name.startswith("external_"):
            return ("外部MCP", "🌐")
        return ("自建MCP", "🔌")
    if source_type == "skill":
        if source_name.startswith("external_") or name.startswith("external_skill_"):
            return ("外部Skill", "📥")
        return ("自建Skill", "📦")
    if source_type == "function":
        return ("本地Tool", "🔧")
    return ("未知", "❓")


def main():
    project_root = Path(__file__).parent
    db_path = str(project_root / "EduSupervisor.db")
    set_db_path(db_path)

    workspace = project_root / "workspace"
    for sub in ["processed", "reports", "exports"]:
        (workspace / sub).mkdir(parents=True, exist_ok=True)

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    registry = ToolRegistry()
    register_all_local_tools(registry)

    skill_adapter = SkillAdapter(project_root / "skills")
    for spec in skill_adapter.load_all():
        registry.register(spec)

    skill_adapter.load_external_skills(project_root / "installed_external_skills")
    for spec in skill_adapter.external_specs:
        registry.register(spec)

    mcp_adapter = MCPAdapter(
        project_root / "mcp_servers",
        project_root / "external_mcp" / "external_mcp_config.json",
        workspace,
        db_path,
    )
    mcp_adapter.start_all()
    for spec in mcp_adapter.to_tool_specs():
        registry.register(spec)

    requirements = OrderedDict([
        ("本地Tool调用", False),
        ("自建Skill调用", False),
        ("外部Skill调用", False),
        ("自建MCP调用", False),
        ("外部MCP调用", False),
    ])

    agent = UnifiedAgent(client, MODEL_NAME, registry, requirements)
    memory = Memory()

    print("=" * 60)
    print(f"  小宋·教育督学 Agent (EduSupervisor) v1.0")
    print(f"  模型: {MODEL_NAME} | 工具: {registry.count()} 个")
    print("  输入 'quit' 退出 | 'status' 验收进度 | 'clear' 清除上下文")
    print("=" * 60)

    result = memory.load_from_db("default")
    if result["ok"] and result["count"] > 0:
        print(f"  📂 已恢复上次对话({result['count']} 条记录)")
        for m in memory.messages[-4:]:
            role_label = "👤 你" if m["role"] == "user" else "🤖 小宋"
            preview = m["content"][:80].replace('\n', ' ')
            print(f"     {role_label}: {preview}{'...' if len(m.content) > 80 else ''}")
        print()

    try:
        while True:
            task = input("\n> ").strip()
            if not task:
                continue
            if task.lower() == "quit":
                if memory.messages:
                    save_result = memory.save_to_db("default")
                    if save_result["ok"]:
                        print(f"💾 {save_result['msg']}")
                break
            if task.lower() == "status":
                print(agent._requirements_status())
                continue
            if task.lower() == "clear":
                memory = Memory()
                print("✅ 对话上下文已清除")
                continue

            def on_answer(text):
                print(text, end="", flush=True)

            def on_tool(name, reason, source_type, source_name):
                label, icon = _tool_label(name, source_type, source_name)
                print(f"\n  {icon} [{label}] {name}", end="", flush=True)
                if reason:
                    print(f": {reason}", end="", flush=True)

            result = agent.run(task, on_answer_chunk=on_answer, on_tool=on_tool, history=memory.messages)
            if not any(result["requirements"].values()):
                print()
            done = sum(1 for v in result["requirements"].values() if v)
            total = len(result["requirements"])
            print(f"\n[{result['steps']}步 | 验收: {done}/{total}]")

            memory.add_user(task)
            memory.add_assistant(result.get("answer", ""))
    except KeyboardInterrupt:
        if memory.messages:
            save_result = memory.save_to_db("default")
            if save_result["ok"]:
                print(f"\n💾 {save_result['msg']}")
        print("\n再见!")
    finally:
        mcp_adapter.shutdown_all()


if __name__ == "__main__":
    main()
