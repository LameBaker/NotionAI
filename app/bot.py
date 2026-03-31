from __future__ import annotations

import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from app.config import load_access_policy_config
from app.env import EnvConfig
from app.google_client import RealGoogleDirectoryClient
from app.identity import GoogleDirectoryIdentityResolver
from app.llm import ClaudeAnswerGenerator
from app.policy import evaluate_page_access
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
    """Testable core logic: resolve user, check ACL, search, generate answer."""

    def __init__(
        self,
        *,
        identity_resolver,
        vector_store,
        answer_generator: Callable[[str, str], str],
        root_policies: dict,
        root_names: dict,
    ):
        self._identity_resolver = identity_resolver
        self._vector_store = vector_store
        self._answer_generator = answer_generator
        self._root_policies = root_policies
        self._root_names = root_names

    def handle(self, *, user_email: str, question: str) -> QuestionResult:
        t0 = time.time()
        log.info("Question from %s: %r", user_email, question)

        if not user_email:
            return QuestionResult(error="Не удалось определить ваш email. Обратитесь к администратору.")

        try:
            user_ou = self._identity_resolver.resolve_org_unit_by_email(user_email)
        except Exception as exc:
            log.error("OU resolution failed for %s: %s", user_email, exc)
            user_ou = None

        if not user_ou:
            log.warning("No OU for %s", user_email)
            return QuestionResult(error="Не удалось определить ваш отдел. Обратитесь к администратору.")

        log.info("User %s → OU: %s", user_email, user_ou)

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

        # Over-fetch proportionally — if user sees few roots, most results get filtered
        total_roots = len(self._root_policies)
        allowed_count = len(allowed_root_ids)
        fetch_count = min(20, 10 * total_roots // max(allowed_count, 1))

        # Search and filter by allowed roots
        raw_chunks = self._vector_store.search(question, n_results=fetch_count)
        authorized_chunks = [c for c in raw_chunks if c.root_id in allowed_root_ids]
        filtered_count = len(raw_chunks) - len(authorized_chunks)

        log.info(
            "Search: %d found, %d authorized%s",
            len(raw_chunks),
            len(authorized_chunks),
            f", {filtered_count} filtered by ACL" if filtered_count else "",
        )
        for i, c in enumerate(authorized_chunks[:5]):
            rname = self._root_names.get(c.root_id, c.root_id[:8])
            log.info("  Chunk %d: [%s] %s...", i + 1, rname, c.text[:80])

        if not authorized_chunks:
            return QuestionResult(error="К сожалению, я не нашёл релевантную информацию по вашему вопросу.")

        # Build context from authorized chunks only
        context = "\n\n".join(c.text for c in authorized_chunks[:5])

        try:
            answer = self._answer_generator(question, context)
        except Exception:
            log.exception("LLM error")
            return QuestionResult(error="Ошибка при генерации ответа. Попробуйте позже.")

        elapsed = time.time() - t0
        log.info("Answered in %.1fs (%d chars)", elapsed, len(answer))

        return QuestionResult(answer=answer)


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

    handler = QuestionHandler(
        identity_resolver=identity_resolver,
        vector_store=vector_store,
        answer_generator=answer_generator,
        root_policies=root_policies,
        root_names=root_names,
    )

    dedup = _ThreadSafeDedup(maxsize=1000)
    rate_limiter = _RateLimiter()

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

        say(result.answer if result.answer else result.error)

    socket_handler = SocketModeHandler(app, env.slack_app_token)
    return app, socket_handler
