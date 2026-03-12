from __future__ import annotations

from typing import Protocol

from app.models import RootAccessPolicy
from app.policy import evaluate_page_access
from app.retrieval import RetrievalChunk, build_authorized_context, filter_authorized_chunks
from app.slack_adapter import format_answer_response


class IdentityResolver(Protocol):
    def resolve_org_unit_by_email(self, email: str) -> str | None:
        ...


class Retriever(Protocol):
    def search(self, query: str) -> list[RetrievalChunk]:
        ...


class AnswerGenerator(Protocol):
    def __call__(self, question: str, context: str) -> str:
        ...


class NotionAIService:
    def __init__(
        self,
        *,
        identity_resolver: IdentityResolver,
        retriever: Retriever,
        answer_generator: AnswerGenerator,
    ) -> None:
        self._identity_resolver = identity_resolver
        self._retriever = retriever
        self._answer_generator = answer_generator

    def answer_question(
        self,
        *,
        user_email: str,
        question: str,
        root_policies_by_page_id: dict[str, RootAccessPolicy],
        source_metadata_by_page_id: dict[str, dict],
    ) -> dict:
        user_ou = self._identity_resolver.resolve_org_unit_by_email(user_email)
        if user_ou is None:
            return format_answer_response("", [])

        raw_results = self._retriever.search(question)

        allowed_page_ids = {
            page_id
            for page_id, root_policy in root_policies_by_page_id.items()
            if evaluate_page_access(user_email=user_email, user_ou=user_ou, root_policy=root_policy)
        }

        authorized_chunks = filter_authorized_chunks(raw_results, allowed_page_ids=allowed_page_ids)
        if not authorized_chunks:
            return format_answer_response("", [])

        context = build_authorized_context(raw_results, allowed_page_ids=allowed_page_ids)
        answer_text = self._answer_generator(question, context)

        ordered_page_ids: list[str] = []
        seen: set[str] = set()
        for chunk in authorized_chunks:
            if chunk.page_id not in seen:
                seen.add(chunk.page_id)
                ordered_page_ids.append(chunk.page_id)

        sources = [
            source_metadata_by_page_id[page_id]
            for page_id in ordered_page_ids
            if page_id in source_metadata_by_page_id
        ]

        return format_answer_response(answer_text, sources)
