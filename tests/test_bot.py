"""Tests for QuestionHandler — the core bot logic."""
from __future__ import annotations

from unittest.mock import MagicMock

from app.bot import QuestionHandler, QuestionResult
from app.models import RootAccessPolicy
from app.retrieval import RetrievalChunk


HR_ROOT_ID = "00000000-0000-0000-0000-000000000001"
DEV_ROOT_ID = "00000000-0000-0000-0000-000000000002"
CURRENCY_ROOT_ID = "00000000-0000-0000-0000-000000000003"


def _make_handler(
    *,
    ou: str | None = "/Development",
    chunks: list[RetrievalChunk] | None = None,
    llm_answer: str = "Test answer",
) -> QuestionHandler:
    identity = MagicMock()
    identity.resolve_org_unit_by_email.return_value = ou

    vector_store = MagicMock()
    vector_store.search.return_value = chunks or []

    answer_gen = MagicMock(return_value=llm_answer)

    root_policies = {
        HR_ROOT_ID: RootAccessPolicy(
            name="HR", page_id=HR_ROOT_ID,
            allow_ou=("/Development", "/Management", "/Sales"),
            allow_users=(),
        ),
        DEV_ROOT_ID: RootAccessPolicy(
            name="Development", page_id=DEV_ROOT_ID,
            allow_ou=("/Development", "/Product"),
            allow_users=(),
        ),
        CURRENCY_ROOT_ID: RootAccessPolicy(
            name="Currency Supply", page_id=CURRENCY_ROOT_ID,
            allow_ou=("/Currency supply",),
            allow_users=(),
        ),
    }
    root_names = {pid: p.name for pid, p in root_policies.items()}

    reranker = MagicMock()
    reranker.rerank.side_effect = lambda q, chunks, top_k=5: chunks[:top_k]

    return QuestionHandler(
        identity_resolver=identity,
        vector_store=vector_store,
        answer_generator=answer_gen,
        reranker=reranker,
        root_policies=root_policies,
        root_names=root_names,
    )


def test_empty_email_returns_error():
    h = _make_handler()
    result = h.handle(user_email="", question="test")
    assert result.error
    assert "email" in result.error.lower()


def test_ou_not_found_returns_error():
    h = _make_handler(ou=None)
    result = h.handle(user_email="user@test.com", question="test")
    assert result.error
    assert "отдел" in result.error.lower()


def test_unauthorized_user_gets_no_access():
    h = _make_handler(ou="/Outsource")
    result = h.handle(user_email="outsource@test.com", question="test")
    assert result.error
    assert "доступ" in result.error.lower()


def test_no_relevant_chunks_returns_not_found():
    h = _make_handler(ou="/Development", chunks=[])
    result = h.handle(user_email="dev@test.com", question="test")
    assert result.error
    assert "не нашёл" in result.error.lower()


def test_authorized_user_gets_answer():
    chunks = [
        RetrievalChunk(page_id="p1", chunk_id="c1", text="Отпуск через Zoho", root_id=HR_ROOT_ID),
    ]
    h = _make_handler(ou="/Development", chunks=chunks, llm_answer="Зайди в Zoho.")
    result = h.handle(user_email="dev@test.com", question="Как взять отпуск?")
    assert result.answer == "Зайди в Zoho."
    assert not result.error


def test_acl_filters_unauthorized_root_chunks():
    chunks = [
        RetrievalChunk(page_id="p1", chunk_id="c1", text="Secret currency data", root_id=CURRENCY_ROOT_ID),
        RetrievalChunk(page_id="p2", chunk_id="c2", text="Dev standards", root_id=DEV_ROOT_ID),
    ]
    h = _make_handler(ou="/Development", chunks=chunks, llm_answer="Dev answer")

    result = h.handle(user_email="dev@test.com", question="test")
    assert result.answer == "Dev answer"

    # Verify LLM received only authorized chunk
    answer_gen = h._answer_generator
    context = answer_gen.call_args[0][1]
    assert "Dev standards" in context
    assert "Secret currency" not in context


def test_currency_user_sees_only_currency():
    chunks = [
        RetrievalChunk(page_id="p1", chunk_id="c1", text="HR stuff", root_id=HR_ROOT_ID),
        RetrievalChunk(page_id="p2", chunk_id="c2", text="Dev stuff", root_id=DEV_ROOT_ID),
        RetrievalChunk(page_id="p3", chunk_id="c3", text="Currency data", root_id=CURRENCY_ROOT_ID),
    ]
    h = _make_handler(ou="/Currency supply", chunks=chunks, llm_answer="Currency answer")

    result = h.handle(user_email="currency@test.com", question="test")
    assert result.answer == "Currency answer"

    context = h._answer_generator.call_args[0][1]
    assert "Currency data" in context
    assert "HR stuff" not in context
    assert "Dev stuff" not in context


def test_llm_error_returns_error_message():
    chunks = [
        RetrievalChunk(page_id="p1", chunk_id="c1", text="Some text", root_id=HR_ROOT_ID),
    ]
    h = _make_handler(ou="/Development", chunks=chunks)
    h._answer_generator.side_effect = RuntimeError("API down")

    result = h.handle(user_email="dev@test.com", question="test")
    assert result.error
    assert "ошибка" in result.error.lower()
