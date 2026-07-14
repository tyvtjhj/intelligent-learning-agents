from dataclasses import dataclass
from openai import OpenAI


@dataclass
class LLMBrain:
    client: OpenAI
    model_name: str

    def reply(self, messages: list[dict[str, str]], max_tokens: int = 1024) -> str:
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return resp.choices[0].message.content
