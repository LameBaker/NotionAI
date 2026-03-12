# Decisions

## 2026-03-12

### D-001: Single Slack Bot for MVP
Use one Slack bot with internal ACL filtering.

### D-002: OU-Based Access Source
Use Google Workspace OU (`orgUnitPath`) as primary access signal.

### D-003: Deny-by-Default
When no allow rule matches, access is denied.

### D-004: Hybrid ACL Management
Use root policies in YAML and page-level Notion tags for local overrides.

### D-005: Pilot Roots
Pilot with `HR` and `Development` roots.

### D-006: In-Memory-First Retrieval Contract
Use a minimal in-memory retrieval chunk model during MVP implementation to validate ACL filtering behavior before adding a vector DB.

### D-007: Transport-Agnostic Slack Formatting
Keep Slack response formatting SDK-free and return a simple payload contract so message transport can be added later without changing core logic.

### D-008: Service Orchestration by Dependency Injection
Wire identity, policy, retrieval, and formatter through injected collaborators for deterministic unit tests and minimal runtime coupling.

### D-009: SDK-Free Adapter Boundaries in Integration Phase
Implement Slack/Google/Notion boundaries as thin adapter layers over injected client interfaces before adding real SDK/runtime wiring.

### D-010: Deterministic Ingestion Failure Recording
Ingestion entrypoint must skip malformed payloads safely and return deterministic failure records for testable behavior.

### D-011: Safe Empty Local Flow Fallback
Local flow converts malformed Slack input and adapter-boundary failures to an explicit safe empty payload shape.
