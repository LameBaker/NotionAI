from __future__ import annotations

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from app.config import load_access_policy_config
from app.env import EnvConfig
from app.google_client import RealGoogleDirectoryClient
from app.identity import GoogleDirectoryIdentityResolver
from app.llm import ClaudeAnswerGenerator
from app.policy import evaluate_page_access
from app.vector_store import ChromaVectorStore


def create_bot(env: EnvConfig) -> tuple[App, SocketModeHandler]:
    app = App(token=env.slack_bot_token)

    config = load_access_policy_config("configs/access_policies.yaml")
    root_policies = {root.page_id: root for root in config.roots}

    google_client = RealGoogleDirectoryClient(
        credentials_path=env.google_credentials_path,
        admin_subject=env.google_admin_subject,
    )
    identity_resolver = GoogleDirectoryIdentityResolver(
        client=google_client,
        corporate_domain="overgear.com",
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

        user_id = event.get("user", "")
        user_info = client.users_info(user=user_id)
        user_email = user_info["user"]["profile"].get("email", "")

        if not user_email:
            say("Не удалось определить ваш email. Обратитесь к администратору.")
            return

        try:
            user_ou = identity_resolver.resolve_org_unit_by_email(user_email)
        except Exception:
            user_ou = None

        if not user_ou:
            say("Не удалось определить ваш отдел. Обратитесь к администратору.")
            return

        # Find which roots this user can access
        allowed_root_ids = set()
        for root_page_id, policy in root_policies.items():
            if evaluate_page_access(
                user_email=user_email,
                user_ou=user_ou,
                root_policy=policy,
            ):
                allowed_root_ids.add(root_page_id)

        if not allowed_root_ids:
            say("У вас нет доступа к данным. Обратитесь к администратору.")
            return

        # Search and filter by allowed roots
        raw_chunks = vector_store.search(question, n_results=10)
        authorized_chunks = [c for c in raw_chunks if c.root_id in allowed_root_ids]

        if not authorized_chunks:
            say("К сожалению, я не нашёл релевантную информацию по вашему вопросу.")
            return

        # Build context from authorized chunks only
        context = "\n\n".join(c.text for c in authorized_chunks[:5])

        try:
            answer = answer_generator(question, context)
        except Exception as exc:
            say(f"Ошибка при генерации ответа: {exc}")
            return

        say(answer)

    handler = SocketModeHandler(app, env.slack_app_token)
    return app, handler
