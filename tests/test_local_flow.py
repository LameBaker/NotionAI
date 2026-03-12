from app.models import RootAccessPolicy
from app.retrieval import RetrievalChunk
from app.service import NotionAIService
from app.local_flow import run_local_flow


class FakeIdentityResolver:
    def __init__(self, org_unit: str | None):
        self.org_unit = org_unit

    def resolve_org_unit_by_email(self, email: str) -> str | None:
        return self.org_unit


class FakeRetriever:
    def __init__(self, chunks: list[RetrievalChunk]):
        self._chunks = chunks

    def search(self, query: str) -> list[RetrievalChunk]:
        return list(self._chunks)


class RecordingAnswerGenerator:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def __call__(self, question: str, context: str) -> str:
        self.calls.append((question, context))
        return f"Answer from context: {context}"


def _root_policy(name: str, page_id: str, allow_ou: list[str]) -> RootAccessPolicy:
    return RootAccessPolicy(name=name, page_id=page_id, allow_ou=allow_ou, allow_users=[])


def test_run_local_flow_authorized_end_to_end() -> None:
    service = NotionAIService(
        identity_resolver=FakeIdentityResolver(org_unit="/Development/Backend"),
        retriever=FakeRetriever(
            [
                RetrievalChunk(page_id="page-dev", chunk_id="c1", text="Deploy docs"),
                RetrievalChunk(page_id="page-hr", chunk_id="c2", text="SECRET salary"),
            ]
        ),
        answer_generator=RecordingAnswerGenerator(),
    )

    event = {
        "type": "app_mention",
        "text": "How do I deploy?",
        "user_email": "dev1@company.com",
        "channel": "C123",
    }

    payload = run_local_flow(
        event,
        service=service,
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
                "text": "raw should never be exposed",
            },
            "page-hr": {
                "title": "Payroll",
                "path": "/HR/Payroll",
                "last_edited_time": "2026-03-09T11:00:00.000Z",
                "page_id": "page-hr",
            },
        },
    )

    assert "Deploy docs" in payload["text"]
    assert "SECRET" not in payload["text"]
    assert payload["sources"] == [
        {
            "title": "Deploy Guide",
            "path": "/Development/Deploy",
            "last_edited_time": "2026-03-10T11:00:00.000Z",
            "page_id": "page-dev",
        }
    ]


def test_run_local_flow_returns_safe_empty_payload_when_no_authorized_chunks() -> None:
    answer_generator = RecordingAnswerGenerator()
    service = NotionAIService(
        identity_resolver=FakeIdentityResolver(org_unit="/Development"),
        retriever=FakeRetriever([RetrievalChunk(page_id="page-hr", chunk_id="c1", text="SECRET payroll")]),
        answer_generator=answer_generator,
    )

    event = {
        "type": "app_mention",
        "text": "What is payroll policy?",
        "user_email": "dev1@company.com",
        "channel": "C123",
    }

    payload = run_local_flow(
        event,
        service=service,
        root_policies_by_page_id={"page-hr": _root_policy("HR", "page-hr", ["/HR"] )},
        source_metadata_by_page_id={
            "page-hr": {
                "title": "Payroll",
                "path": "/HR/Payroll",
                "last_edited_time": "2026-03-09T11:00:00.000Z",
                "page_id": "page-hr",
            }
        },
    )

    assert payload == {"text": "", "sources": []}
    assert answer_generator.calls == []
