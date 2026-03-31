"""Query rewriting: LLM expands/clarifies user query before search."""
from __future__ import annotations

import logging

from anthropic import Anthropic

log = logging.getLogger("notionai.query")

_REWRITE_PROMPT = (
    "Ты помогаешь улучшить поисковый запрос для корпоративной wiki Overgear (игровая компания).\n"
    "Перепиши запрос пользователя так, чтобы он лучше находил релевантные документы:\n"
    "- Разверни аббревиатуры (ТК → Трудовой кодекс, ДМС → добровольное медицинское страхование)\n"
    "- Добавь синонимы через запятую\n"
    "- Сохрани оригинальный смысл\n"
    "- Ответь ТОЛЬКО переписанным запросом, без объяснений\n"
)


class QueryRewriter:
    def __init__(self, *, api_key: str, model: str = "claude-haiku-4-5") -> None:
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def rewrite(self, query: str) -> str:
        """Rewrite query for better search. Returns original on failure."""
        if len(query) > 200:
            return query  # Long queries don't need expansion

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=200,
                system=_REWRITE_PROMPT,
                messages=[{"role": "user", "content": query}],
            )
            rewritten = response.content[0].text.strip()
            if rewritten and len(rewritten) < 500:
                log.info("Query rewrite: %r → %r", query, rewritten)
                return rewritten
        except Exception:
            log.debug("Query rewrite failed, using original", exc_info=True)

        return query
