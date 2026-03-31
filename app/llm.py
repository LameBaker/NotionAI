from __future__ import annotations

import logging

from anthropic import (
    Anthropic,
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    RateLimitError,
)

log = logging.getLogger("notionai.llm")

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
    """Claude-based answer generator. Used by app/bot.py."""

    def __init__(self, *, api_key: str, model: str = "claude-haiku-4-5-20251001") -> None:
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def __call__(self, question: str, context: str) -> str:
        prompt = build_prompt(question=question, context=context)
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except AuthenticationError:
            log.error("Anthropic API key is invalid or expired")
            raise
        except RateLimitError:
            log.warning("Anthropic rate limit hit")
            raise
        except APIConnectionError:
            log.error("Failed to connect to Anthropic API")
            raise
        except APIStatusError as exc:
            log.error("Anthropic API error %d: %s", exc.status_code, exc.message)
            raise
