"""Query rewriting: abbreviation expansion + LLM clarification before search."""
from __future__ import annotations

import logging
import re
from pathlib import Path

import yaml
from anthropic import Anthropic

log = logging.getLogger("notionai.query")

_REWRITE_PROMPT = (
    "Ты помогаешь улучшить поисковый запрос для корпоративной wiki Overgear (игровая компания).\n"
    "Перепиши запрос пользователя так, чтобы он лучше находил релевантные документы:\n"
    "- Разверни аббревиатуры если есть\n"
    "- Добавь синонимы через запятую\n"
    "- Сохрани оригинальный смысл\n"
    "- Ответь ТОЛЬКО переписанным запросом, без объяснений\n"
)


def _load_abbreviations(path: str = "configs/abbreviations.yaml") -> dict[str, str]:
    """Load abbreviation dictionary from YAML."""
    config_path = Path(path)
    if not config_path.exists():
        return {}
    try:
        data = yaml.safe_load(config_path.read_text())
        return data.get("abbreviations", {})
    except Exception:
        log.debug("Failed to load abbreviations", exc_info=True)
        return {}


def expand_abbreviations(query: str, abbreviations: dict[str, str]) -> str:
    """Expand known abbreviations in query text."""
    if not abbreviations:
        return query

    expanded = query
    for abbr, full in abbreviations.items():
        # Match whole word only (case-insensitive)
        pattern = re.compile(r"\b" + re.escape(abbr) + r"\b", re.IGNORECASE)
        if pattern.search(expanded):
            expanded = pattern.sub(f"{abbr} ({full})", expanded)

    if expanded != query:
        log.info("Abbreviation expansion: %r → %r", query, expanded)

    return expanded


class QueryRewriter:
    def __init__(self, *, api_key: str, model: str = "claude-haiku-4-5") -> None:
        self._client = Anthropic(api_key=api_key)
        self._model = model
        self._abbreviations = _load_abbreviations()

    def rewrite(self, query: str) -> str:
        """Expand abbreviations, then rewrite via LLM. Returns original on failure."""
        # Step 1: Expand known abbreviations (free, instant)
        expanded = expand_abbreviations(query, self._abbreviations)

        # Step 2: LLM rewrite for synonyms and clarification
        if len(expanded) > 200:
            return expanded

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=200,
                system=_REWRITE_PROMPT,
                messages=[{"role": "user", "content": expanded}],
            )
            rewritten = response.content[0].text.strip()
            if rewritten and len(rewritten) < 500:
                log.info("LLM rewrite: %r → %r", expanded, rewritten)
                return rewritten
        except Exception:
            log.debug("LLM rewrite failed, using expanded query", exc_info=True)

        return expanded
