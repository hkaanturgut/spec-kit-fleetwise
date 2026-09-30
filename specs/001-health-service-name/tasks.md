---

description: "Task list template for feature implementation"
---

# Tasks: Health Endpoint Service Name

**Input**: Design documents from `/specs/001-health-service-name/`

**Prerequisites**: plan.md, spec.md, data-model.md, contracts/health.md, quickstart.md

**Tests**: Explicitly requested - spec FR-006 requires regression coverage, and the plan's
Test-First constitution gate requires the existing test extended and failing before the
implementation change.

**Organization**: Single user story (P1) - there is only one scope item per spec.md.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1)
- Include exact file paths in descriptions

## Path Conventions

- Existing single ASP.NET Core project: `src/FleetWise.Api/Program.cs`
- Existing xUnit test project: `tests/FleetWise.Tests/SeedAndApiTests.cs`
- No new files, folders, or projects are created by this feature.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: None required - no new project, dependency, or tooling changes.

*(Intentionally empty: existing `src/FleetWise.Api` and `tests/FleetWise.Tests` projects already
build and run; no setup tasks are needed per plan.md Scale/Scope.)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: None required - `/health` has no shared models, auth, or routing changes to add.

*(Intentionally empty: per data-model.md there are no entities, and per plan.md Constitution
Check items I/II/V are N/A. Proceed directly to User Story 1.)*

---

## Phase 3: User Story 1 - Identify which service answered a health check (Priority: P1) 🎯 MVP

**Goal**: `GET /health` returns HTTP 200 with JSON body `{"status":"ok","service":"FleetWise.Api"}`,
with every other endpoint's behavior unchanged.

**Independent Test**: Call `GET /health` anonymously; verify HTTP 200 and a JSON body containing
both `status: "ok"` and `service: "FleetWise.Api"`.

### Tests for User Story 1 ⚠️

> Write this test FIRST. Run it and confirm it FAILS (the `service` field does not exist yet)
> before touching `Program.cs`.

- [X] T001 [US1] Extend `ApiTests.Health_is_ok` in `tests/FleetWise.Tests/SeedAndApiTests.cs` to assert HTTP 200, `status: "ok"`, and `service: "FleetWise.Api"` (FR-003, FR-006). Run `dotnet test tests/FleetWise.Tests --filter Health_is_ok` and confirm failure before implementation.

### Implementation for User Story 1

- [X] T002 [US1] Add the fixed literal `service = "FleetWise.Api"` alongside `status = "ok"` in the `/health` handler in `src/FleetWise.Api/Program.cs`. Preserve its route, HTTP 200, anonymous access, and every other endpoint. No configuration or dependency changes.

### Verification for User Story 1

- [X] T003 [US1] Run `dotnet test tests/FleetWise.Tests --filter Health_is_ok`, then `dotnet test`. Confirm the new assertion passes and the full suite has zero regressions (SC-002, SC-003).

**Checkpoint**: User Story 1 is fully functional, tested, and independently verifiable. This is
the entire feature scope - no further phases are required.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: None required - plan.md Scale/Scope states this is a one-line implementation change
plus one extended test, with no other scope. No polish tasks are added.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Empty - no dependencies.
- **Foundational (Phase 2)**: Empty - no dependencies.
- **User Story 1 (Phase 3)**: T001 (test, must fail first) → T002 (implementation) → T003
  (verification). Strictly sequential; no parallelism within this story (single shared file per
  step, and each step depends on the previous step's file state).

### Within User Story 1

- T001 must be written and confirmed FAILING before T002 (Test-First constitution gate).
- T002 depends on T001 existing.
- T003 depends on T002 being complete.

### Parallel Opportunities

- None. All three tasks touch the sequential test→implement→verify flow described in the
  feature's input ("Keep the task list small: test, implement, verify."); no [P] tasks apply.

---

## Implementation Strategy

### MVP First (and Only) Scope

1. T001: Extend the existing test to assert the new `service` field; confirm it fails.
2. T002: Add the one-line `service = "FleetWise.Api"` field to the `/health` handler.
3. T003: Confirm the extended test passes and the full suite has zero regressions.
4. Done - this is the complete feature; no further phases, stories, or polish tasks exist.

---

## Notes

- No `[P]` markers are used: this feature is a single sequential test → implement → verify chain
  in two existing files.
- No new files, dependencies, or projects are introduced per plan.md.
- Verify the test fails before implementing (T001), and passes with zero regressions after
  (T003).
- Commit only after the final workflow publication approval.
