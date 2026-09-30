# Feature Specification: Health Endpoint Service Name

**Feature Branch**: `demo/delivery-20260930-201143-26d0ce05`

**Created**: 2026-09-30

**Status**: Draft

**Input**: User description: "Extend GET /health to return the fixed service name FleetWise.Api alongside status ok. Preserve HTTP 200, anonymous access, and all other endpoints. Add regression coverage in the existing test. No dependency, database or architecture changes. Keep the task list small: test, implement, verify."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Identify which service answered a health check (Priority: P1)

An operator or monitoring system calls `GET /health` to confirm the API is running and wants the response to clearly identify which service it came from, without adding any new call or credential.

**Why this priority**: This is the entire scope of the feature; there is only one user journey.

**Independent Test**: Call `GET /health` anonymously and verify the JSON body contains both `status: "ok"` and `service: "FleetWise.Api"`, with an HTTP 200 response.

**Acceptance Scenarios**:

1. **Given** the API is running, **When** an unauthenticated client sends `GET /health`, **Then** the response is HTTP 200 with a JSON body containing `status: "ok"` and `service: "FleetWise.Api"`.
2. **Given** the API is running, **When** any other existing endpoint is called, **Then** its behavior, status codes, and payload shape are unchanged.

---

### Edge Cases

- No authentication/authorization is required or added - `/health` remains anonymously accessible.
- The service name is a fixed, hardcoded value (`FleetWise.Api`), not derived from configuration or environment, so there is no missing-value case to handle.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `GET /health` MUST return HTTP 200 on success, unchanged from current behavior.
- **FR-002**: `GET /health` MUST return a JSON body containing `status: "ok"` (existing field, unchanged).
- **FR-003**: `GET /health` MUST return a JSON body additionally containing `service: "FleetWise.Api"` (new field, fixed string value).
- **FR-004**: `GET /health` MUST remain anonymously accessible (no authentication/authorization required).
- **FR-005**: All other existing endpoints MUST remain behaviorally unchanged (no routes, schemas, or status codes altered outside `/health`).
- **FR-006**: The existing automated test suite MUST include regression coverage asserting both `status` and `service` fields on `/health`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A `GET /health` call returns HTTP 200 with both `status: "ok"` and `service: "FleetWise.Api"` present in the response body, 100% of the time.
- **SC-002**: The full existing automated test suite passes after the change, with zero regressions in previously passing tests.
- **SC-003**: No endpoint other than `/health` changes its response contract as a result of this change.

## Assumptions

- "Fixed service name" means a hardcoded literal string `FleetWise.Api` in the response, not read from configuration, environment variables, or assembly metadata.
- The regression test is added to the existing test file/class already covering `/health` (`Health_is_ok`), rather than a new test file.
- No versioning, health-check library, or additional health fields (e.g., dependency checks) are introduced - this is purely an additive field on the existing response.
