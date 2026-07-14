import sys
from pathlib import Path
from dataclasses import dataclass, field
from openai import OpenAI

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import API_KEY, BASE_URL, MODEL_NAME
from core.memory import Memory
from core.llm_brain import LLMBrain


@dataclass
class MiniAgent:
    name: str
    system_prompt: str
    brain: LLMBrain
    memory: Memory = field(default_factory=Memory)

    def __post_init__(self) -> None:
        if not any(m["role"] == "system" for m in self.memory.messages):
            self.memory.add_system(self.system_prompt)

    def run_once(self, user_goal: str, max_tokens: int = 1024) -> str:
        self.memory.add_user(user_goal)
        reply = self.brain.reply(self.memory.recent(), max_tokens=max_tokens)
        self.memory.add_assistant(reply)
        return reply

    def status(self) -> dict:
        return {
            "name": self.name,
            "total_messages": len(self.memory.messages),
            "memory_snapshot": self.memory.snapshot()
        }


def create_default_agent() -> MiniAgent:
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    brain = LLMBrain(client=client, model_name=MODEL_NAME)

    return MiniAgent(
        name="EduSupervisor-Mini",
        system_prompt="你是教育督学 Agent，一个帮助学生学习的 AI 助手。你耐心、专业，善于用简单语言讲清楚复杂概念。",
        brain=brain,
    )


if __name__ == "__main__":
    agent = create_default_agent()
    print(f">>> {agent.name} 已启动")
    print(f">>> 模型: {MODEL_NAME}")
    print(">>> 输入 'quit' 退出, 'status' 查看状态\n")

    while True:
        try:
            task = input("\n📝 > ").strip()
            if not task:
                continue
            if task.lower() == "quit":
                break
            if task.lower() == "status":
                s = agent.status()
                print(f"  Agent: {s['name']}  |  消息数: {s['total_messages']}")
                continue

            reply = agent.run_once(task)
            print(f"\n🤖 {reply}")

        except KeyboardInterrupt:
            print("\n再见!")
            break
        except Exception as e:
            print(f"\n[错误] {e}")
