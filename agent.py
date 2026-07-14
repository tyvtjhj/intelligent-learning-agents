import sys
from pathlib import Path
from collections import OrderedDict
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent))

from config import API_KEY, BASE_URL, MODEL_NAME
from core.tool_registry import ToolRegistry
from core.agent import UnifiedAgent
from core.adapters.skill_adapter import SkillAdapter
from core.adapters.mcp_adapter import MCPAdapter
from tools.local_tools import register_all_local_tools
from db.connection import set_db_path, init_db as _init_db


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

    print("=" * 60)
    print(f"  教育督学 Agent (EduSupervisor) v1.0")
    print(f"  模型: {MODEL_NAME} | 工具: {registry.count()} 个")
    print("  输入 'quit' 退出 | 'status' 验收进度")
    print("=" * 60)

    try:
        while True:
            task = input("\n> ").strip()
            if not task:
                continue
            if task.lower() == "quit":
                break
            if task.lower() == "status":
                print(agent._requirements_status())
                continue

            result = agent.run(task)
            print(f"\n{result['answer']}")
            done = sum(1 for v in result["requirements"].values() if v)
            total = len(result["requirements"])
            print(f"[{result['steps']}步 | 验收: {done}/{total}]")
    except KeyboardInterrupt:
        print("\n再见!")
    finally:
        mcp_adapter.shutdown_all()


if __name__ == "__main__":
    main()
