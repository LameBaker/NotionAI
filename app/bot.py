from __future__ import annotations

import logging
import time

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


def create_bot(env: EnvConfig) -> tuple[App, SocketModeHandler]:
    app = App(token=env.slack_bot_token)

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
    vector_store = ChromaVectorStore(persist_dir=".chroma_data")
    answer_generator = ClaudeAnswerGenerator(api_key=env.anthropic_api_key)

    @app.event("message")
    def handle_dm(event, say, client):
        if event.get("channel_type") != "im":
            return
        if event.get("bot_id") or event.get("subtype"):
            return

        question = event.get("text", "").strip()
        if not question:
            return

        t0 = time.time()
        user_id = event.get("user", "")
        user_info = client.users_info(user=user_id)
        user_email = user_info["user"]["profile"].get("email", "")

        log.info(f"Question from {user_email}: {question!r}")

        if not user_email:
            say("Не удалось определить ваш email. Обратитесь к администратору.")
            return

        try:
            user_ou = identity_resolver.resolve_org_unit_by_email(user_email)
        except Exception as exc:
            log.error(f"OU resolution failed for {user_email}: {exc}")
            user_ou = None

        if not user_ou:
            log.warning(f"No OU for {user_email}")
            say("Не удалось определить ваш отдел. Обратитесь к администратору.")
            return

        log.info(f"User {user_email} → OU: {user_ou}")

        # Find which roots this user can access
        allowed_root_ids = set()
        for root_page_id, policy in root_policies.items():
            if evaluate_page_access(
                user_email=user_email,
                user_ou=user_ou,
                root_policy=policy,
            ):
                allowed_root_ids.add(root_page_id)

        allowed_names = [root_names.get(rid, rid) for rid in allowed_root_ids]
        log.info(f"ACL: {len(allowed_root_ids)} roots allowed: {', '.join(sorted(allowed_names))}")

        if not allowed_root_ids:
            say("У вас нет доступа к данным. Обратитесь к администратору.")
            return

        # Search and filter by allowed roots
        raw_chunks = vector_store.search(question, n_results=10)
        authorized_chunks = [c for c in raw_chunks if c.root_id in allowed_root_ids]
        filtered_count = len(raw_chunks) - len(authorized_chunks)

        log.info(
            f"Search: {len(raw_chunks)} found, {len(authorized_chunks)} authorized"
            f"{f', {filtered_count} filtered by ACL' if filtered_count else ''}"
        )
        for i, c in enumerate(authorized_chunks[:5]):
            rname = root_names.get(c.root_id, c.root_id[:8])
            log.info(f"  Chunk {i+1}: [{rname}] {c.text[:80]}...")

        if not authorized_chunks:
            say("К сожалению, я не нашёл релевантную информацию по вашему вопросу.")
            return

        # Build context from authorized chunks only
        context = "\n\n".join(c.text for c in authorized_chunks[:5])

        try:
            answer = answer_generator(question, context)
        except Exception as exc:
            log.error(f"LLM error: {exc}")
            say(f"Ошибка при генерации ответа: {exc}")
            return

        elapsed = time.time() - t0
        log.info(f"Answered in {elapsed:.1f}s ({len(answer)} chars)")

        say(answer)

    handler = SocketModeHandler(app, env.slack_app_token)
    return app, handler
