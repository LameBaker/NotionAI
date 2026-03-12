from app.models import RootAccessPolicy
from app.retrieval import RetrievalChunk
from app.service import NotionAIService


class FakeIdentityResolver:
    def __init__(self, org_unit: str | None):
        self.org_unit = org_unit
        self.calls: list[str] = []

    def resolve_org_unit_by_email(self, email: str) -> str | None:
        self.calls.append(email)
        return self.org_unit


class RecordingAnswerGenerator:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def __call__(self, question: str, context: str) -> str:
        self.calls.append((question, context))
        return f"Answer from context: {context}"


class FakeRetriever:
    def __init__(self, chunks: list[RetrievalChunk]):
        self.chunks = chunks
        self.calls: list[str] = []

    def search(self, query: str) -> list[RetrievalChunk]:
        self.calls.append(query)
        return list(self.chunks)


def _root_policy(name: str, page_id: str, allow_ou: list[str]) -> RootAccessPolicy:
    return RootAccessPolicy(name=name, page_id=page_id, allow_ou=allow_ou, allow_users=[])


def test_service_returns_answer_with_only_authorized_sources() -> None:
    retriever = FakeRetriever(
        [
            RetrievalChunk(page_id="page-dev", chunk_id="c1", text="Dev playbook"),
            RetrievalChunk(page_id="page-hr", chunk_id="c2", text="SECRET payroll"),
        ]
    )
    identity = FakeIdentityResolver(org_unit="/Development/Backend")
    answer_generator = RecordingAnswerGenerator()

    service = NotionAIService(
        identity_resolver=identity,
        retriever=retriever,
        answer_generator=answer_generator,
    )

    response = service.answer_question(
        user_email="dev1@company.com",
        question="How do I deploy?",
        root_policies_by_page_id={
            "page-dev": _root_policy("Development", "page-dev", ["/Development"]),
            "page-hr": _root_policy("HR", "page-hr", ["/HR"]),
        },
        source_metadata_by_page_id={
            "page-dev": {
                "title": "Deploy Guide",
                "path": "/Development/Deploy",
                "last_edited_time": "2026-03-10T11:00:00.000Z",
                "page_id": "page-dev",
                "text": "raw snippet should not leak",
            },
            "page-hr": {
                "title": "Payroll",
                "path": "/HR/Payroll",
                "last_edited_time": "2026-03-09T11:00:00.000Z",
                "page_id": "page-hr",
                "text": "SECRET",
            },
        },
    )

    assert identity.calls == ["dev1@company.com"]
    assert retriever.calls == ["How do I deploy?"]
    assert len(answer_generator.calls) == 1
    assert "Dev playbook" in response["answer_text"]
    assert "SECRET" not in response["answer_text"]
    assert response["sources"] == [
        {
            "title": "Deploy Guide",
            "path": "/Development/Deploy",
            "last_edited_time": "2026-03-10T11:00:00.000Z",
            "page_id": "page-dev",
        }
    ]


def test_service_returns_safe_empty_shape_when_no_authorized_chunks() -> None:
    retriever = FakeRetriever(
        [
            RetrievalChunk(page_id="page-hr", chunk_id="c1", text="SECRET payroll"),
        ]
    )
    identity = FakeIdentityResolver(org_unit="/Development")
    answer_generator = RecordingAnswerGenerator()

    service = NotionAIService(
        identity_resolver=identity,
        retriever=retriever,
        answer_generator=answer_generator,
    )

    response = service.answer_question(
        user_email="dev1@company.com",
        question="What is payroll policy?",
        root_policies_by_page_id={
            "page-hr": _root_policy("HR", "page-hr", ["/HR"]),
        },
        source_metadata_by_page_id={
            "page-hr": {
                "title": "Payroll",
                "path": "/HR/Payroll",
                "last_edited_time": "2026-03-09T11:00:00.000Z",
                "page_id": "page-hr",
            }
        },
    )

    assert response == {"answer_text": "", "sources": []}
    assert answer_generator.calls == []


def test_service_denies_root_allowed_page_when_acl_restricted_without_page_allows() -> None:
    retriever = FakeRetriever(
        [
            RetrievalChunk(page_id="page-open", chunk_id="c1", text="Should be denied"),
        ]
    )
    identity = FakeIdentityResolver(org_unit="/Development")
    answer_generator = RecordingAnswerGenerator()

    service = NotionAIService(
        identity_resolver=identity,
        retriever=retriever,
        answer_generator=answer_generator,
    )

    response = service.answer_question(
        user_email="dev1@company.com",
        question="Can I read this?",
        root_policies_by_page_id={
            "page-open": _root_policy("Open", "page-open", ["/"]),
        },
        source_metadata_by_page_id={
            "page-open": {
                "title": "Open Page",
                "path": "/General/Open",
                "last_edited_time": "2026-03-12T10:00:00.000Z",
                "page_id": "page-open",
                "acl_restricted": True,
            }
        },
    )

    assert response == {"answer_text": "", "sources": []}
    assert answer_generator.calls == []


def test_service_allows_root_denied_page_with_page_level_acl_allow_users_or_ou() -> None:
    retriever = FakeRetriever(
        [
            RetrievalChunk(page_id="page-users", chunk_id="c1", text="Allowed by user override"),
            RetrievalChunk(page_id="page-ou", chunk_id="c2", text="Allowed by OU override"),
        ]
    )
    identity = FakeIdentityResolver(org_unit="/Development/Backend")
    answer_generator = RecordingAnswerGenerator()

    service = NotionAIService(
        identity_resolver=identity,
        retriever=retriever,
        answer_generator=answer_generator,
    )

    response = service.answer_question(
        user_email="dev1@company.com",
        question="Can I read overrides?",
        root_policies_by_page_id={
            "page-users": _root_policy("HR", "page-users", ["/HR"]),
            "page-ou": _root_policy("HR", "page-ou", ["/HR"]),
        },
        source_metadata_by_page_id={
            "page-users": {
                "title": "Override User",
                "path": "/HR/OverrideUser",
                "last_edited_time": "2026-03-12T10:00:00.000Z",
                "page_id": "page-users",
                "acl_allow_users": ["dev1@company.com"],
            },
            "page-ou": {
                "title": "Override OU",
                "path": "/HR/OverrideOu",
                "last_edited_time": "2026-03-12T10:05:00.000Z",
                "page_id": "page-ou",
                "acl_allow_ou": ["/Development"],
            },
        },
    )

    assert "Allowed by user override" in response["answer_text"]
    assert "Allowed by OU override" in response["answer_text"]
    assert response["sources"] == [
        {
            "title": "Override User",
            "path": "/HR/OverrideUser",
            "last_edited_time": "2026-03-12T10:00:00.000Z",
            "page_id": "page-users",
        },
        {
            "title": "Override OU",
            "path": "/HR/OverrideOu",
            "last_edited_time": "2026-03-12T10:05:00.000Z",
            "page_id": "page-ou",
        },
    ]
