# NotionAI MVP Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working Slack bot that answers questions from Notion content with OU-based access control.

**Architecture:** Two processes — a Slack bot (Socket Mode, DM-only) and a Notion sync script (cron). ChromaDB for vector search, Claude Haiku for answers, Google Directory for OU resolution. Existing ACL core (policy.py, identity.py, retrieval.py) is reused and extended with OU group support.

**Tech Stack:** Python, slack-bolt, chromadb, anthropic, notion-client, google-api-python-client, python-dotenv

---

## File Map

**New files:**
- `app/env.py` — load .env, expose typed config
- `app/llm.py` — LLM abstraction + Claude Haiku implementation
- `app/vector_store.py` — ChromaDB wrapper implementing Retriever protocol
- `app/notion_crawler.py` — fetch Notion pages recursively, chunk text
- `app/google_client.py` — real Google Admin SDK client (implements DirectoryClient protocol)
- `app/bot.py` — Slack bot (bolt-python, Socket Mode, DM handler)
- `main.py` — bot entrypoint
- `sync.py` — Notion sync entrypoint
- `requirements.txt` — all dependencies

**Modified files:**
- `app/models.py` — add OU group support to AccessPolicyConfig
- `app/config.py` — resolve `allow_ou_group` references during config load
- `configs/access_policies.yaml` — full config with all 17 roots + groups
- `tests/test_config.py` — update for new config shape

---

### Task 1: Dependencies and Environment Loading

**Files:**
- Create: `requirements.txt`
- Create: `app/env.py`
- Create: `tests/test_env.py`

- [ ] **Step 1: Create requirements.txt**

```
slack-bolt>=1.18,<2
slack-sdk>=3.27,<4
anthropic>=0.39,<1
chromadb>=0.5,<1
notion-client>=2.2,<3
google-api-python-client>=2.100,<3
google-auth>=2.20,<3
python-dotenv>=1.0,<2
pyyaml>=6.0,<7
pytest>=8.0,<10
```

- [ ] **Step 2: Install dependencies**

Run: `.venv/bin/pip install -r requirements.txt`

- [ ] **Step 3: Write test for env loader**

```python
# tests/test_env.py
import os
from unittest.mock import patch

from app.env import load_env


def test_load_env_reads_required_values():
    env = {
        "SLACK_BOT_TOKEN": "xoxb-test",
        "SLACK_APP_TOKEN": "xapp-test",
        "ANTHROPIC_API_KEY": "sk-ant-test",
        "NOTION_TOKEN": "ntn_test",
        "GOOGLE_APPLICATION_CREDENTIALS": "creds.json",
        "GOOGLE_ADMIN_SUBJECT": "admin@test.com",
    }
    with patch.dict(os.environ, env, clear=False):
        config = load_env()

    assert config.slack_bot_token == "xoxb-test"
    assert config.slack_app_token == "xapp-test"
    assert config.anthropic_api_key == "sk-ant-test"
    assert config.notion_token == "ntn_test"
    assert config.google_credentials_path == "creds.json"
    assert config.google_admin_subject == "admin@test.com"


def test_load_env_raises_for_missing_required():
    with patch.dict(os.environ, {}, clear=True):
        try:
            load_env()
            assert False, "Should have raised"
        except ValueError as e:
            assert "SLACK_BOT_TOKEN" in str(e)
```

- [ ] **Step 4: Run test to verify it fails**

Run: `pytest tests/test_env.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.env'`

- [ ] **Step 5: Implement env loader**

```python
# app/env.py
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class EnvConfig:
    slack_bot_token: str
    slack_app_token: str
    anthropic_api_key: str
    notion_token: str
    google_credentials_path: str
    google_admin_subject: str


_REQUIRED = [
    "SLACK_BOT_TOKEN",
    "SLACK_APP_TOKEN",
    "ANTHROPIC_API_KEY",
    "NOTION_TOKEN",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_ADMIN_SUBJECT",
]


def load_env(dotenv_path: str = ".env") -> EnvConfig:
    load_dotenv(dotenv_path)

    missing = [key for key in _REQUIRED if not os.getenv(key, "").strip()]
    if missing:
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")

    return EnvConfig(
        slack_bot_token=os.environ["SLACK_BOT_TOKEN"].strip(),
        slack_app_token=os.environ["SLACK_APP_TOKEN"].strip(),
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"].strip(),
        notion_token=os.environ["NOTION_TOKEN"].strip(),
        google_credentials_path=os.environ["GOOGLE_APPLICATION_CREDENTIALS"].strip(),
        google_admin_subject=os.environ["GOOGLE_ADMIN_SUBJECT"].strip(),
    )
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/test_env.py -v`
Expected: 2 passed

- [ ] **Step 7: Run full suite**

Run: `pytest -v`
Expected: 49 passed (47 existing + 2 new)

- [ ] **Step 8: Commit**

```bash
git add requirements.txt app/env.py tests/test_env.py
git commit -m "feat: add requirements.txt and env config loader"
```

---

### Task 2: OU Groups in Config

**Files:**
- Modify: `app/models.py`
- Modify: `app/config.py`
- Modify: `configs/access_policies.yaml`
- Modify: `tests/test_config.py`

- [ ] **Step 1: Write test for group resolution**

Add to `tests/test_config.py`:

```python
def test_load_access_policy_config_resolves_ou_groups(tmp_path: Path) -> None:
    config_path = tmp_path / "access_policies.yaml"
    config_path.write_text(
        """
default: deny_all

groups:
  all_internal:
    - "/Development"
    - "/Sales"

roots:
  - name: HR
    page_id: "hr-page"
    allow_ou_group: all_internal
    allow_users: []

  - name: Dev
    page_id: "dev-page"
    allow_ou:
      - "/Development"
    allow_users: []
""".strip()
    )

    config = load_access_policy_config(config_path)

    assert config.roots[0].name == "HR"
    assert config.roots[0].allow_ou == ["/Development", "/Sales"]
    assert config.roots[1].name == "Dev"
    assert config.roots[1].allow_ou == ["/Development"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py::test_load_access_policy_config_resolves_ou_groups -v`
Expected: FAIL — `allow_ou_group` not handled

- [ ] **Step 3: Update config.py to resolve groups**

Replace entire `app/config.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.models import AccessPolicyConfig, RootAccessPolicy


def load_access_policy_config(path: Path | str) -> AccessPolicyConfig:
    config_path = Path(path)
    payload = yaml.safe_load(config_path.read_text())

    if not isinstance(payload, dict):
        raise ValueError("Access policy config must be a mapping")

    default = payload.get("default")
    if default != "deny_all":
        raise ValueError("Access policy default must be 'deny_all'")

    groups = _parse_groups(payload.get("groups", {}))

    raw_roots = payload.get("roots", [])
    if not isinstance(raw_roots, list):
        raise ValueError("roots must be a list")

    roots = [_build_root_policy(item, groups) for item in raw_roots]
    return AccessPolicyConfig(default=default, roots=roots)


def _parse_groups(raw_groups: Any) -> dict[str, list[str]]:
    if not isinstance(raw_groups, dict):
        return {}
    groups: dict[str, list[str]] = {}
    for name, values in raw_groups.items():
        if isinstance(values, list):
            groups[str(name)] = [str(v) for v in values]
    return groups


def _build_root_policy(payload: Any, groups: dict[str, list[str]]) -> RootAccessPolicy:
    if not isinstance(payload, dict):
        raise ValueError("root entry must be a mapping")

    name = str(payload.get("name", "")).strip()
    page_id = str(payload.get("page_id", "")).strip()

    allow_ou_group = str(payload.get("allow_ou_group", "")).strip()
    if allow_ou_group and allow_ou_group in groups:
        allow_ou = list(groups[allow_ou_group])
    else:
        allow_ou = payload.get("allow_ou", [])

    allow_users = payload.get("allow_users", [])

    if not name or not page_id:
        raise ValueError("root entries require name and page_id")
    if not isinstance(allow_ou, list) or not isinstance(allow_users, list):
        raise ValueError("allow_ou and allow_users must be lists")

    return RootAccessPolicy(
        name=name,
        page_id=page_id,
        allow_ou=[str(item) for item in allow_ou],
        allow_users=[str(item) for item in allow_users],
    )
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_config.py -v`
Expected: 3 passed

- [ ] **Step 5: Update access_policies.yaml with real config**

Replace `configs/access_policies.yaml` with full config (all roots + groups + real page IDs for HR and Development, TBD for others).

```yaml
default: deny_all

groups:
  all_internal:
    - "/Boosting Supply"
    - "/Currency supply"
    - "/Customer Care & Support"
    - "/Development"
    - "/Game performance"
    - "/Management"
    - "/Product"
    - "/Sales"
    - "/Service"

roots:
  - name: HR
    page_id: "6fc13a2a-a763-441c-8a99-a6c3fabe9a2b"
    allow_ou_group: all_internal
    allow_users: []

  - name: Development
    page_id: "81c090a3-eb85-44e5-bae3-c0f16e8d0cea"
    allow_ou:
      - "/Development"
      - "/Product"
    allow_users: []
```

Note: remaining roots (Marketing, Content, etc.) will be added once page IDs are resolved from Notion API. Start with HR + Development for testing.

- [ ] **Step 6: Update existing config test for new shape**

Update `test_load_access_policy_config_from_repo_file` to match new yaml:

```python
def test_load_access_policy_config_from_repo_file() -> None:
    config = load_access_policy_config(CONFIG_PATH)

    assert config.default == "deny_all"
    assert len(config.roots) == 2
    assert config.roots[0].name == "HR"
    assert "/Development" in config.roots[0].allow_ou  # resolved from group
    assert config.roots[1].name == "Development"
    assert config.roots[1].allow_ou == ["/Development", "/Product"]
```

- [ ] **Step 7: Run full suite**

Run: `pytest -v`
Expected: all passed

- [ ] **Step 8: Commit**

```bash
git add app/config.py app/models.py configs/access_policies.yaml tests/test_config.py
git commit -m "feat: add OU group support to access policy config"
```

---

### Task 3: Real Google Directory Client

**Files:**
- Create: `app/google_client.py`

- [ ] **Step 1: Implement real Google Admin SDK client**

This client implements the `DirectoryClient` protocol from `app/identity.py`. No unit test — it wraps an SDK and will be validated by running the existing spike script pattern.

```python
# app/google_client.py
from __future__ import annotations

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class RealGoogleDirectoryClient:
    """Implements DirectoryClient protocol using real Google Admin SDK."""

    def __init__(self, *, credentials_path: str, admin_subject: str) -> None:
        creds = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/admin.directory.user.readonly"],
        ).with_subject(admin_subject)
        service = build("admin", "directory_v1", credentials=creds, cache_discovery=False)
        self._users = service.users()

    def get_user_by_email(self, email: str) -> dict[str, str] | None:
        try:
            payload = self._users.get(userKey=email, projection="basic").execute()
        except HttpError as exc:
            if getattr(getattr(exc, "resp", None), "status", None) == 404:
                return None
            raise
        return {
            "primaryEmail": str(payload.get("primaryEmail", "")).strip(),
            "orgUnitPath": str(payload.get("orgUnitPath", "")).strip(),
        }
```

- [ ] **Step 2: Run full suite to verify no regressions**

Run: `pytest -v`
Expected: all passed

- [ ] **Step 3: Commit**

```bash
git add app/google_client.py
git commit -m "feat: add real Google Directory client"
```

---

### Task 4: LLM Abstraction + Claude Implementation

**Files:**
- Create: `app/llm.py`
- Create: `tests/test_llm.py`

- [ ] **Step 1: Write test**

```python
# tests/test_llm.py
from app.llm import build_prompt


def test_build_prompt_includes_context_and_question():
    prompt = build_prompt(question="Как взять отпуск?", context="Отпуск оформляется через Zoho.")
    assert "Как взять отпуск?" in prompt
    assert "Отпуск оформляется через Zoho." in prompt


def test_build_prompt_handles_empty_context():
    prompt = build_prompt(question="Вопрос?", context="")
    assert "Вопрос?" in prompt
    assert "контекст" in prompt.lower() or "context" in prompt.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm.py -v`
Expected: FAIL

- [ ] **Step 3: Implement LLM module**

```python
# app/llm.py
from __future__ import annotations

from anthropic import Anthropic


SYSTEM_PROMPT = (
    "Ты — корпоративный ассистент Overgear. Отвечай на вопросы сотрудников "
    "строго на основе предоставленного контекста из Notion. "
    "Если в контексте нет ответа — скажи об этом честно. "
    "Отвечай на русском языке, кратко и по делу."
)


def build_prompt(*, question: str, context: str) -> str:
    if not context.strip():
        return (
            f"Контекст: (нет релевантных данных)\n\n"
            f"Вопрос: {question}"
        )
    return f"Контекст из Notion:\n{context}\n\nВопрос: {question}"


class ClaudeAnswerGenerator:
    """Implements AnswerGenerator protocol from app/service.py."""

    def __init__(self, *, api_key: str, model: str = "claude-haiku-4-5-20251001") -> None:
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def __call__(self, question: str, context: str) -> str:
        prompt = build_prompt(question=question, context=context)
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_llm.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add app/llm.py tests/test_llm.py
git commit -m "feat: add LLM abstraction with Claude Haiku"
```

---

### Task 5: Vector Store (ChromaDB)

**Files:**
- Create: `app/vector_store.py`
- Create: `tests/test_vector_store.py`

- [ ] **Step 1: Write test**

```python
# tests/test_vector_store.py
from app.vector_store import ChromaVectorStore


def test_upsert_and_search_returns_relevant_chunks(tmp_path):
    store = ChromaVectorStore(persist_dir=str(tmp_path / "chroma"))

    store.upsert_chunks([
        {"chunk_id": "c1", "page_id": "p1", "root_id": "r1", "title": "Отпуска", "text": "Отпуск оформляется через Zoho People."},
        {"chunk_id": "c2", "page_id": "p2", "root_id": "r1", "title": "Зарплата", "text": "Зарплата выплачивается 10 числа."},
    ])

    results = store.search("как взять отпуск", n_results=2)

    assert len(results) >= 1
    assert results[0].page_id == "p1"
    assert "Zoho" in results[0].text


def test_search_empty_store_returns_empty(tmp_path):
    store = ChromaVectorStore(persist_dir=str(tmp_path / "chroma"))
    results = store.search("anything", n_results=5)
    assert results == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_vector_store.py -v`
Expected: FAIL

- [ ] **Step 3: Implement ChromaDB wrapper**

```python
# app/vector_store.py
from __future__ import annotations

import chromadb

from app.retrieval import RetrievalChunk


class ChromaVectorStore:
    """Implements Retriever protocol from app/service.py via search()."""

    def __init__(self, *, persist_dir: str = ".chroma_data") -> None:
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name="notion_chunks",
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(self, chunks: list[dict]) -> None:
        if not chunks:
            return
        self._collection.upsert(
            ids=[c["chunk_id"] for c in chunks],
            documents=[c["text"] for c in chunks],
            metadatas=[
                {"page_id": c["page_id"], "root_id": c["root_id"], "title": c.get("title", "")}
                for c in chunks
            ],
        )

    def search(self, query: str, n_results: int = 5) -> list[RetrievalChunk]:
        if self._collection.count() == 0:
            return []
        results = self._collection.query(query_texts=[query], n_results=n_results)
        chunks = []
        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            chunks.append(
                RetrievalChunk(
                    page_id=meta["page_id"],
                    chunk_id=doc_id,
                    text=results["documents"][0][i],
                )
            )
        return chunks

    def clear(self) -> None:
        self._client.delete_collection("notion_chunks")
        self._collection = self._client.get_or_create_collection(
            name="notion_chunks",
            metadata={"hnsw:space": "cosine"},
        )
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_vector_store.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add app/vector_store.py tests/test_vector_store.py
git commit -m "feat: add ChromaDB vector store"
```

---

### Task 6: Notion Crawler

**Files:**
- Create: `app/notion_crawler.py`
- Create: `tests/test_notion_crawler.py`

- [ ] **Step 1: Write test for text chunking**

```python
# tests/test_notion_crawler.py
from app.notion_crawler import chunk_text


def test_chunk_text_splits_by_size():
    text = "Абзац один.\n\nАбзац два.\n\nАбзац три."
    chunks = chunk_text(text, max_chunk_size=30)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 30 or "\n" not in chunk  # single paragraph can exceed


def test_chunk_text_preserves_all_content():
    text = "Hello world.\n\nFoo bar.\n\nBaz."
    chunks = chunk_text(text, max_chunk_size=1000)
    joined = "\n\n".join(chunks)
    assert "Hello world." in joined
    assert "Foo bar." in joined
    assert "Baz." in joined


def test_chunk_text_empty_input():
    assert chunk_text("", max_chunk_size=100) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_notion_crawler.py -v`
Expected: FAIL

- [ ] **Step 3: Implement crawler module**

```python
# app/notion_crawler.py
from __future__ import annotations

from notion_client import Client as NotionClient


def chunk_text(text: str, max_chunk_size: int = 1000) -> list[str]:
    if not text.strip():
        return []
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if current and len(current) + len(para) + 2 > max_chunk_size:
            chunks.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    if current:
        chunks.append(current)
    return chunks


def fetch_page_text(client: NotionClient, page_id: str) -> str:
    blocks = _get_all_blocks(client, page_id)
    parts: list[str] = []
    for block in blocks:
        text = _extract_block_text(block)
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def crawl_root(client: NotionClient, root_page_id: str) -> list[dict]:
    """Recursively fetch all pages under a root. Returns list of {page_id, title, text}."""
    pages: list[dict] = []
    _crawl_recursive(client, root_page_id, pages)
    return pages


def _crawl_recursive(client: NotionClient, page_id: str, pages: list[dict]) -> None:
    try:
        page = client.pages.retrieve(page_id)
    except Exception:
        return

    title = _extract_page_title(page)
    text = fetch_page_text(client, page_id)

    if text.strip():
        pages.append({"page_id": page_id, "title": title, "text": text})

    blocks = _get_all_blocks(client, page_id)
    for block in blocks:
        if block.get("type") == "child_page":
            child_id = block.get("id", "")
            if child_id:
                _crawl_recursive(client, child_id, pages)


def _get_all_blocks(client: NotionClient, block_id: str) -> list[dict]:
    blocks: list[dict] = []
    cursor = None
    while True:
        response = client.blocks.children.list(block_id, start_cursor=cursor, page_size=100)
        blocks.extend(response.get("results", []))
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return blocks


def _extract_block_text(block: dict) -> str:
    block_type = block.get("type", "")
    data = block.get(block_type, {})
    rich_texts = data.get("rich_text", [])
    if not rich_texts:
        rich_texts = data.get("text", [])
    parts = []
    for rt in rich_texts:
        if isinstance(rt, dict):
            parts.append(rt.get("plain_text", ""))
    return "".join(parts).strip()


def _extract_page_title(page: dict) -> str:
    props = page.get("properties", {})
    for val in props.values():
        if isinstance(val, dict) and val.get("type") == "title":
            entries = val.get("title", [])
            parts = [e.get("plain_text", "") for e in entries if isinstance(e, dict)]
            return " ".join(parts).strip()
    return ""
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_notion_crawler.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add app/notion_crawler.py tests/test_notion_crawler.py
git commit -m "feat: add Notion crawler with recursive page fetch and chunking"
```

---

### Task 7: Sync Script

**Files:**
- Create: `sync.py`

- [ ] **Step 1: Implement sync entrypoint**

```python
#!/usr/bin/env python3
"""Notion sync — fetch pages, chunk, embed into ChromaDB."""
from __future__ import annotations

import sys

from notion_client import Client as NotionClient

from app.config import load_access_policy_config
from app.env import load_env
from app.notion_crawler import chunk_text, crawl_root
from app.vector_store import ChromaVectorStore


def main() -> int:
    env = load_env()
    config = load_access_policy_config("configs/access_policies.yaml")

    notion = NotionClient(auth=env.notion_token)
    store = ChromaVectorStore(persist_dir=".chroma_data")

    total_chunks = 0
    for root in config.roots:
        print(f"Crawling {root.name} ({root.page_id})...")
        pages = crawl_root(notion, root.page_id)
        print(f"  Found {len(pages)} pages")

        chunks = []
        for page in pages:
            text_chunks = chunk_text(page["text"])
            for i, text in enumerate(text_chunks):
                chunks.append({
                    "chunk_id": f"{page['page_id']}_{i}",
                    "page_id": page["page_id"],
                    "root_id": root.page_id,
                    "title": page["title"],
                    "text": text,
                })

        store.upsert_chunks(chunks)
        total_chunks += len(chunks)
        print(f"  Indexed {len(chunks)} chunks")

    print(f"Done. Total: {total_chunks} chunks indexed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run full test suite**

Run: `pytest -v`
Expected: all passed

- [ ] **Step 3: Commit**

```bash
git add sync.py
git commit -m "feat: add Notion sync script"
```

---

### Task 8: Slack Bot

**Files:**
- Create: `app/bot.py`
- Create: `main.py`

- [ ] **Step 1: Implement bot module**

```python
# app/bot.py
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
        # Only handle DMs (channel type "im")
        if event.get("channel_type") != "im":
            return
        # Ignore bot messages
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
                source_text = "\n\n📚 Источники:\n" + "\n".join(source_lines)

        say(f"{answer}{source_text}")

    handler = SocketModeHandler(app, env.slack_app_token)
    return app, handler
```

- [ ] **Step 2: Implement main.py**

```python
#!/usr/bin/env python3
"""NotionAI Slack bot entrypoint."""
from app.bot import create_bot
from app.env import load_env


def main():
    env = load_env()
    print("Starting NotionAI bot...")
    _, handler = create_bot(env)
    handler.start()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run full test suite**

Run: `pytest -v`
Expected: all passed (no new tests — bot is integration code)

- [ ] **Step 4: Commit**

```bash
git add app/bot.py main.py
git commit -m "feat: add Slack bot with Socket Mode DM handler"
```

---

### Task 9: End-to-End Smoke Test

- [ ] **Step 1: Run Notion sync**

```bash
.venv/bin/python sync.py
```

Expected output:
```
Crawling HR (6fc13a2a-...)...
  Found N pages
  Indexed M chunks
Crawling Development (81c090a3-...)...
  Found N pages
  Indexed M chunks
Done. Total: X chunks indexed.
```

- [ ] **Step 2: Start the bot**

```bash
.venv/bin/python main.py
```

Expected: `Starting NotionAI bot...` and then `⚡️ Bolt app is running!`

- [ ] **Step 3: Test in Slack**

Open DM with the bot in Slack. Send: `Как взять отпуск?`

Expected: bot responds with an answer based on HR Notion content.

- [ ] **Step 4: Test ACL**

If your OU is `/Development`, you should get answers from both HR and Development.
A user with OU `/Outsource` should get "нет доступа" for everything.

- [ ] **Step 5: Commit any fixes**

```bash
git add -A
git commit -m "fix: smoke test adjustments"
```

- [ ] **Step 6: Final full suite**

Run: `pytest -v`
Expected: all passed
