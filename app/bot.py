from __future__ import annotations

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from app.config import load_access_policy_config
from app.env import EnvConfig
from app.google_client import RealGoogleDirectoryClient
from app.identity import GoogleDirectoryIdentityResolver
from app.llm import ClaudeAnswerGenerator
from app.service import NotionAIService
from app.vector_store import ChromaVectorStore


def create_bot(env: EnvConfig) -> tuple[App, SocketModeHandler]:
    app = App(token=env.slack_bot_token)

    config = load_access_policy_config("configs/access_policies.yaml")
    root_policies_by_page_id = {root.page_id: root for root in config.roots}

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

    service = NotionAIService(
        identity_resolver=identity_resolver,
        retriever=vector_store,
        answer_generator=answer_generator,
    )

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
            result = service.answer_question(
                user_email=user_email,
                question=question,
                root_policies_by_page_id=root_policies_by_page_id,
                source_metadata_by_page_id={},
            )
        except Exception as exc:
            say(f"Произошла ошибка: {exc}")
            return

        answer = result.get("answer_text", "")
        if not answer:
            say("К сожалению, я не нашёл информацию по вашему вопросу или у вас нет доступа к релевантным данным.")
            return

        sources = result.get("sources", [])
        source_text = ""
        if sources:
            source_lines = [f"• {s.get('title', 'Untitled')}" for s in sources if s.get("title")]
            if source_lines:
                source_text = "\n\n Источники:\n" + "\n".join(source_lines)

        say(f"{answer}{source_text}")

    handler = SocketModeHandler(app, env.slack_app_token)
    return app, handler
