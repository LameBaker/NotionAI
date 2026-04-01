from __future__ import annotations

import logging
import re
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from notion_client import Client as NotionClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from app.config import load_access_policy_config
from app.env import EnvConfig
from app.google_client import RealGoogleDirectoryClient
from app.identity import GoogleDirectoryIdentityResolver
from app.llm import ClaudeAnswerGenerator
from app.policy import evaluate_page_access
from app.hybrid_search import HybridSearcher
from app.query_rewriter import QueryRewriter
from app.reranker import BGEReranker
from app.retrieval import RetrievalChunk
from app.semantic_cache import SemanticCache
from app.vector_store import ChromaVectorStore

log = logging.getLogger("notionai")

_PROJECT_ROOT = Path(__file__).parent.parent

# Rate limit: max requests per user per window
_RATE_LIMIT_MAX = 10
_RATE_LIMIT_WINDOW = 60  # seconds


@dataclass
class QuestionResult:
    answer: str = ""
    error: str = ""
    sources: list[dict] = field(default_factory=list)


class _ThreadSafeDedup:
    """Thread-safe bounded set for message deduplication."""

    def __init__(self, maxsize: int = 1000) -> None:
        self._lock = threading.Lock()
        self._cache: OrderedDict[str, None] = OrderedDict()
        self._maxsize = maxsize

    def check_and_add(self, key: str) -> bool:
        """Returns True if key was already seen (duplicate)."""
        with self._lock:
            if key in self._cache:
                return True
            self._cache[key] = None
            if len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)
            return False


class _RateLimiter:
    """Simple per-user sliding window rate limiter."""

    def __init__(self, max_requests: int = _RATE_LIMIT_MAX, window: float = _RATE_LIMIT_WINDOW) -> None:
        self._lock = threading.Lock()
        self._requests: dict[str, list[float]] = {}
        self._max = max_requests
        self._window = window

    def is_allowed(self, user_id: str) -> bool:
        now = time.time()
        with self._lock:
            timestamps = self._requests.get(user_id, [])
            timestamps = [t for t in timestamps if now - t < self._window]
            if len(timestamps) >= self._max:
                self._requests[user_id] = timestamps
                return False
            timestamps.append(now)
            self._requests[user_id] = timestamps
            return True


class QuestionHandler:
    """Core logic: resolve user, check ACL, search, rerank, generate answer with citations."""

    def __init__(
        self,
        *,
        identity_resolver,
        searcher,
        answer_generator: Callable[[str, str], str],
        reranker,
        query_rewriter=None,
        cache=None,
        root_policies: dict,
        root_names: dict,
    ):
        self._identity_resolver = identity_resolver
        self._searcher = searcher
        self._answer_generator = answer_generator
        self._reranker = reranker
        self._query_rewriter = query_rewriter
        self._cache = cache
        self._root_policies = root_policies
        self._root_names = root_names

    def handle(self, *, user_email: str, question: str) -> QuestionResult:
        t0 = time.time()
        log.info("Question from %s: %r", user_email, question)

        if not user_email:
            return QuestionResult(error="Не удалось определить ваш email. Обратитесь к администратору.")

        # Retry OU resolution (transient SSL/network errors)
        user_ou = None
        for attempt in range(3):
            try:
                user_ou = self._identity_resolver.resolve_org_unit_by_email(user_email)
                break
            except Exception as exc:
                log.warning("OU resolution attempt %d failed for %s: %s", attempt + 1, user_email, exc)
                if attempt < 2:
                    time.sleep(1)

        if not user_ou:
            log.warning("No OU for %s", user_email)
            return QuestionResult(error="Не удалось определить ваш отдел. Обратитесь к администратору.")

        log.info("User %s → OU: %s", user_email, user_ou)

        # Check semantic cache (scoped by OU — different departments get different answers)
        if self._cache:
            cached = self._cache.get(question, user_ou=user_ou)
            if cached:
                log.info("Cache hit for %s (OU: %s)", user_email, user_ou)
                return QuestionResult(answer=cached["answer"], sources=cached.get("sources", []))

        # Find which roots this user can access
        allowed_root_ids = set()
        for root_page_id, policy in self._root_policies.items():
            if evaluate_page_access(
                user_email=user_email,
                user_ou=user_ou,
                root_policy=policy,
            ):
                allowed_root_ids.add(root_page_id)

        allowed_names = [self._root_names.get(rid, rid) for rid in allowed_root_ids]
        log.info("ACL: %d roots allowed: %s", len(allowed_root_ids), ", ".join(sorted(allowed_names)))

        if not allowed_root_ids:
            return QuestionResult(error="У вас нет доступа к данным. Обратитесь к администратору.")

        # Query rewriting for better search
        search_query = question
        if self._query_rewriter:
            search_query = self._query_rewriter.rewrite(question)

        # Over-fetch for reranking — get top-20, ACL filter, rerank to top-5
        raw_chunks = self._searcher.search(search_query, n_results=20)
        authorized_chunks = [c for c in raw_chunks if c.root_id in allowed_root_ids]
        filtered_count = len(raw_chunks) - len(authorized_chunks)

        log.info(
            "Search: %d found, %d authorized%s",
            len(raw_chunks),
            len(authorized_chunks),
            f", {filtered_count} filtered by ACL" if filtered_count else "",
        )

        if not authorized_chunks:
            return QuestionResult(error="К сожалению, я не нашёл релевантную информацию по вашему вопросу.")

        # Rerank authorized chunks for better relevance (with OU boost)
        reranked = self._reranker.rerank(
            question, authorized_chunks, top_k=5,
            user_ou=user_ou, root_names=self._root_names,
        )

        for i, c in enumerate(reranked):
            rname = self._root_names.get(c.root_id, c.root_id[:8])
            log.info("  Chunk %d: [%s] %s — %s...", i + 1, rname, c.title, c.text[:60])

        # Build numbered context for citation — use parent_text for richer LLM context
        context_parts = []
        sources = []
        seen_pages: set[str] = set()
        for i, c in enumerate(reranked):
            context_text = c.parent_text if c.parent_text else c.text
            context_parts.append(f"[{i + 1}] {context_text}")
            if c.page_id not in seen_pages:
                seen_pages.add(c.page_id)
                sources.append({
                    "index": i + 1,
                    "title": c.title,
                    "url": c.page_url,
                    "page_id": c.page_id,
                })

        context = "\n\n".join(context_parts)

        try:
            answer = self._answer_generator(question, context)
        except Exception:
            log.exception("LLM error")
            return QuestionResult(error="Ошибка при генерации ответа. Попробуйте позже.")

        # Cache the answer with sources (scoped by OU)
        if self._cache:
            self._cache.put(question, answer, sources, user_ou=user_ou)

        elapsed = time.time() - t0
        log.info("Answered in %.1fs (%d chars, %d sources)", elapsed, len(answer), len(sources))

        return QuestionResult(answer=answer, sources=sources)


def _format_slack_blocks(result: QuestionResult) -> dict:
    """Format answer as Slack Block Kit with 'Show full text' buttons."""
    if result.error:
        return {"text": result.error}

    blocks: list[dict] = [
        {"type": "section", "text": {"type": "mrkdwn", "text": result.answer[:3000]}},
    ]

    if result.sources:
        source_lines = []
        for s in result.sources:
            title = s.get("title", "Страница")
            url = s.get("url", "")
            if url:
                source_lines.append(f"• <{url}|{title}>")
            else:
                source_lines.append(f"• {title}")

        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "📚 *Источники:*\n" + "\n".join(source_lines)},
        })

        # Add "Show full text" buttons for top sources
        buttons = []
        for s in result.sources[:3]:
            page_id = s.get("page_id", "")
            title = s.get("title", "Страница")
            if page_id:
                buttons.append({
                    "type": "button",
                    "text": {"type": "plain_text", "text": f"📄 {title[:30]}", "emoji": True},
                    "action_id": f"show_full_text_{page_id}",
                    "value": page_id,
                })

        if buttons:
            blocks.append({
                "type": "actions",
                "elements": buttons,
            })

    # Feedback buttons
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "👍 Полезно", "emoji": True},
                "action_id": "feedback_positive",
                "style": "primary",
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "👎 Не то", "emoji": True},
                "action_id": "feedback_negative",
                "style": "danger",
            },
        ],
    })

    return {"blocks": blocks, "text": result.answer[:200]}


def create_bot(env: EnvConfig) -> tuple[App, SocketModeHandler]:
    # Socket Mode uses WebSocket, not HTTP — no request signature verification needed
    app = App(token=env.slack_bot_token, token_verification_enabled=False)

    config = load_access_policy_config(env.config_path)
    root_policies = {root.page_id: root for root in config.roots}
    root_names = {root.page_id: root.name for root in config.roots}

    google_client = RealGoogleDirectoryClient(
        credentials_path=env.google_credentials_path,
        admin_subject=env.google_admin_subject,
    )
    identity_resolver = GoogleDirectoryIdentityResolver(
        client=google_client,
        corporate_domain=env.corporate_domain,
    )
    chroma_path = str(_PROJECT_ROOT / ".chroma_data")
    vector_store = ChromaVectorStore(persist_dir=chroma_path)
    answer_generator = ClaudeAnswerGenerator(api_key=env.anthropic_api_key)
    reranker = BGEReranker()
    query_rewriter = QueryRewriter(api_key=env.anthropic_api_key)

    # Hybrid search: vector + BM25 (BM25 index built lazily from ChromaDB data)
    searcher = HybridSearcher(vector_store=vector_store)
    cache = SemanticCache(vector_store=vector_store)
    notion_client = NotionClient(auth=env.notion_token, timeout_ms=60_000)

    handler = QuestionHandler(
        identity_resolver=identity_resolver,
        searcher=searcher,
        answer_generator=answer_generator,
        reranker=reranker,
        query_rewriter=query_rewriter,
        cache=cache,
        root_policies=root_policies,
        root_names=root_names,
    )

    dedup = _ThreadSafeDedup(maxsize=1000)
    rate_limiter = _RateLimiter()
    # Simple conversation history per user (last question)
    _conversation: dict[str, str] = {}

    @app.event("message")
    def handle_dm(event, say, client):
        if event.get("channel_type") != "im":
            return
        if event.get("bot_id") or event.get("subtype"):
            return

        # Deduplicate Slack event retries (thread-safe)
        msg_id = event.get("client_msg_id", "")
        if msg_id and dedup.check_and_add(msg_id):
            log.debug("Skipping duplicate event %s", msg_id)
            return

        question = event.get("text", "").strip()
        if not question:
            return

        # Built-in commands
        if question.lower() in ("status", "статус", "help", "помощь"):
            chunk_count = vector_store._collection.count()
            root_count = len(config.roots)
            cache_count = cache._collection.count() if cache else 0
            say(
                f"📊 *NotionAI Status*\n"
                f"• Roots: {root_count}\n"
                f"• Chunks indexed: {chunk_count:,}\n"
                f"• Cached answers: {cache_count}\n"
                f"• Model: BGE-M3 + BGE Reranker + Claude Haiku\n\n"
                f"Просто задайте вопрос, и я найду ответ в Notion."
            )
            return

        user_id = event.get("user", "")

        # Rate limit per user
        if not rate_limiter.is_allowed(user_id):
            say("Слишком много запросов. Подождите минуту.")
            return

        try:
            user_info = client.users_info(user=user_id)
            user_email = user_info["user"]["profile"].get("email", "")
        except Exception:
            log.exception("Failed to fetch user info for %s", user_id)
            say("Не удалось определить ваш профиль. Попробуйте позже.")
            return

        result = handler.handle(user_email=user_email, question=question)
        response = _format_slack_blocks(result)
        say(**response)

    # Feedback handlers
    @app.action("feedback_positive")
    def handle_feedback_positive(ack, body):
        ack()
        user = body.get("user", {}).get("name", "unknown")
        log.info("Feedback: 👍 from %s", user)

    @app.action("feedback_negative")
    def handle_feedback_negative(ack, body):
        ack()
        user = body.get("user", {}).get("name", "unknown")
        log.info("Feedback: 👎 from %s", user)

    # Handle @mention in channels
    @app.event("app_mention")
    def handle_mention(event, say, client):
        question = re.sub(r"<@[A-Z0-9]+>\s*", "", event.get("text", "")).strip()
        if not question:
            say(text="Задайте вопрос после @mention.", thread_ts=event.get("ts"))
            return

        user_id = event.get("user", "")
        try:
            user_info = client.users_info(user=user_id)
            user_email = user_info["user"]["profile"].get("email", "")
        except Exception:
            say(text="Не удалось определить ваш профиль.", thread_ts=event.get("ts"))
            return

        result = handler.handle(user_email=user_email, question=question)
        response = _format_slack_blocks(result)
        response["thread_ts"] = event.get("ts")  # Reply in thread
        say(**response)

    @app.action(re.compile(r"show_full_text_.*"))
    def handle_show_full_text(ack, body, client):
        ack()
        action = body["actions"][0]
        page_id = action["value"]
        trigger_id = body["trigger_id"]

        # Show loading modal
        modal_resp = client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "title": {"type": "plain_text", "text": "Загрузка..."},
                "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": "⏳ Подгружаю страницу из Notion..."}}],
            },
        )
        view_id = modal_resp["view"]["id"]

        # Fetch full page text from Notion (live)
        try:
            from app.notion_crawler import _get_all_blocks, _extract_rich_text, _extract_page_title

            page = notion_client.pages.retrieve(page_id)
            title = _extract_page_title(page)
            blocks = _get_all_blocks(notion_client, page_id)

            parts: list[str] = []
            for block in blocks:
                block_type = block.get("type", "")
                if block_type in ("child_page", "child_database"):
                    continue
                text = _extract_rich_text(block)
                if text:
                    parts.append(text)
                # Fetch children (toggles, callouts)
                if block.get("has_children"):
                    bid = block.get("id", "")
                    if bid:
                        children = _get_all_blocks(notion_client, bid)
                        for child in children:
                            ct = _extract_rich_text(child)
                            if ct:
                                parts.append(ct)

            full_text = "\n\n".join(parts)
        except Exception:
            log.exception("Failed to fetch page %s", page_id)
            full_text = "Не удалось загрузить страницу."
            title = "Ошибка"

        # Split into Slack modal blocks (max 50 blocks, 3000 chars each)
        modal_blocks: list[dict] = []
        for i in range(0, len(full_text), 3000):
            chunk = full_text[i : i + 3000]
            modal_blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": chunk},
            })
            if len(modal_blocks) >= 48:
                modal_blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "_...текст обрезан (слишком длинная страница)_"},
                })
                break

        if not modal_blocks:
            modal_blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Страница пустая."}}]

        # Update modal with content
        client.views_update(
            view_id=view_id,
            view={
                "type": "modal",
                "title": {"type": "plain_text", "text": (title or "Страница")[:24]},
                "blocks": modal_blocks,
            },
        )

    socket_handler = SocketModeHandler(app, env.slack_app_token)
    return app, socket_handler
