from __future__ import annotations

from anthropic import Anthropic


SYSTEM_PROMPT = (
    "Ты — корпоративный ассистент Overgear. Отвечай на вопросы сотрудников "
    "строго на основе предоставленного контекста из Notion. "
    "Если в контексте нет ответа — скажи об этом честно. "
    "Отвечай на русском языке, кратко и по делу."
)


def build_prompt(*, question: str, context: str) -> str:
    if not context.strip():
        return (
            f"Контекст: (нет релевантных данных)\n\n"
            f"Вопрос: {question}"
        )
    return f"Контекст из Notion:\n{context}\n\nВопрос: {question}"


class ClaudeAnswerGenerator:
    """Implements AnswerGenerator protocol from app/service.py."""

    def __init__(self, *, api_key: str, model: str = "claude-haiku-4-5-20251001") -> None:
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def __call__(self, question: str, context: str) -> str:
        prompt = build_prompt(question=question, context=context)
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
