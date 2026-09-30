# Tasks: Overdue Maintenance Dispatcher

**Input**: Design documents from `/specs/001-overdue-dispatcher/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/dispatch-api.md

**Tests**: Required. The constitution mandates test-first (Principle III), so every story starts
with failing tests.

**Format**: `[ID] [P?] [Story] Description` where `[P]` means it can run in parallel (different
files, no dependencies).

## Phase 1: Setup

**Purpose**: Confirm the baseline before changing anything.

- [X] T001 Run `dotnet test` and confirm the existing 15 tests pass on a clean checkout
- [X] T002 [P] Add a `TestClock`-based helper to create a second tenant's vehicles and technicians in tests/FleetWise.Tests/TestSupport.cs

---

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: Tenant resolution and the decision entity every story needs.

- [X] T003 Write failing tests for tenant header resolution (missing header, non-numeric, valid) in tests/FleetWise.Tests/DispatchApiTests.cs
- [X] T004 Implement `TenantContext` (reads `X-Tenant-Id`, `X-User-Role`, `X-User-Name`) in src/FleetWise.Api/Services/TenantContext.cs
- [X] T005 [P] Add `DispatchDecision` entity and `DispatchOutcome` enum in src/FleetWise.Api/Models/Entities.cs
- [X] T006 Register `DbSet<DispatchDecision>` with string conversion for `Outcome` in src/FleetWise.Api/Data/FleetWiseDbContext.cs
- [X] T007 [P] Add `DispatchLine` and `TechnicianSuggestion` read models in src/FleetWise.Api/Models/Dispatch.cs

**Checkpoint**: Foundation ready. User stories can begin.

---

## Phase 3: User Story 1 - See what needs service now (Priority: P1) 🎯 MVP

**Goal**: A tenant-scoped list of vehicles whose scheduled services are overdue or due within 7 days.

**Independent Test**: Seeded fleet; list contains exactly the schedule-overdue or due-soon lines for
the requesting tenant and none from the other tenant.

### Tests for User Story 1

- [X] T008 [P] [US1] Failing test: distance-overdue oil change is listed with `KmOverdue` in tests/FleetWise.Tests/DispatcherServiceTests.cs
- [X] T009 [P] [US1] Failing test: date due in 5 days is listed as `DueSoon` in tests/FleetWise.Tests/DispatcherServiceTests.cs
- [X] T010 [P] [US1] Failing test: tenant 1 never sees tenant 2 vehicles in tests/FleetWise.Tests/DispatcherServiceTests.cs
- [X] T011 [P] [US1] Failing test: open work order marks the line `AlreadyHandled` in tests/FleetWise.Tests/DispatcherServiceTests.cs

### Implementation for User Story 1

- [X] T012 [US1] Implement `DispatcherService.GetLinesAsync(tenantId)` due calculation in src/FleetWise.Api/Services/DispatcherService.cs
- [X] T013 [US1] Add `GET /api/dispatch` in src/FleetWise.Api/Controllers/DispatchController.cs
- [X] T014 [US1] Register `DispatcherService` in src/FleetWise.Api/Program.cs

**Checkpoint**: US1 works on its own: the MVP.

---

## Phase 4: User Story 2 - Get a suggested work order (Priority: P2)

**Goal**: Each line carries a technician suggestion.

**Independent Test**: Suggestions name a technician with the required skill, prefer the least busy,
and flag lines where nobody qualifies.

### Tests for User Story 2

- [ ] T015 [P] [US2] Failing test: least-busy qualified technician is suggested, ties by name, in tests/FleetWise.Tests/TechnicianMatcherTests.cs
- [ ] T016 [P] [US2] Failing test: no qualified technician gives an unassigned, flagged suggestion in tests/FleetWise.Tests/TechnicianMatcherTests.cs
- [ ] T016a [P] [US2] Failing test: a qualified technician in another tenant is never suggested (FR-010) in tests/FleetWise.Tests/TechnicianMatcherTests.cs

### Implementation for User Story 2

- [ ] T017 [US2] Implement `TechnicianMatcher.SuggestAsync(tenantId, requiredSkill)`, scoping technicians and work orders by `TenantId`, in src/FleetWise.Api/Services/TechnicianMatcher.cs
- [ ] T018 [US2] Attach suggestions to lines in src/FleetWise.Api/Services/DispatcherService.cs

**Checkpoint**: US1 and US2 work independently.

---

## Phase 5: User Story 3 - Approve before anything is booked (Priority: P3)

**Goal**: Only FleetManagers can approve or reject; approval schedules a work order.

**Independent Test**: Approve one line, reject another; only the approved one becomes a scheduled
work order, and both decisions are recorded.

### Tests for User Story 3

- [ ] T019 [P] [US3] Failing test: approval creates a scheduled work order for the next business day and a decision in tests/FleetWise.Tests/DispatcherServiceTests.cs
- [ ] T020 [P] [US3] Failing test: rejection records a decision and keeps the line in tests/FleetWise.Tests/DispatcherServiceTests.cs
- [ ] T021 [P] [US3] Failing test: non-FleetManager gets 403, second approval gets 409, in tests/FleetWise.Tests/DispatchApiTests.cs

### Implementation for User Story 3

- [ ] T022 [US3] Implement `ApproveAsync` and `RejectAsync` in src/FleetWise.Api/Services/DispatcherService.cs
- [ ] T023 [US3] Add `POST /api/dispatch/approve` and `POST /api/dispatch/reject` in src/FleetWise.Api/Controllers/DispatchController.cs

**Checkpoint**: All user stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T024 [P] Update README API section and docs/architecture.md with the dispatcher
- [ ] T025 Run quickstart.md scenarios end to end

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → user stories. US2 and US3 build on US1's `DispatcherService`.
- Within a story, tests (marked failing) come before implementation.

```text
T001 → T003 → T004 ─┐
T005 → T006 ────────┼→ T012 → T013 → T014 → T017 → T018 → T022 → T023 → T025
T007 ───────────────┘
```

## Parallel Example: User Story 1

```text
T008, T009, T010, T011 can be written in parallel (same file, independent test methods).
```

## Implementation Strategy

1. MVP: Phases 1 to 3, then stop and validate US1 with the quickstart.
2. Add US2, validate; add US3, validate.
3. Polish.

---

## Phase 7: Convergence

- [ ] T026 Return 400 when `X-Tenant-Id` does not match an existing tenant (today a non-existent tenant gets 200 with an empty list) per contracts/dispatch-api.md (partial)

---

## Phase 8: FR-012 - Configurable overdue window per tenant

**Why**: spec.md added FR-012 ("The overdue window is configurable per tenant (default 7 days)")
after US1 shipped. `DispatcherService` currently uses a hardcoded `DueSoonDays = 7` constant
(src/FleetWise.Api/Services/DispatcherService.cs) instead of a per-tenant value, and `Tenant` (per
data-model.md "Existing entities touched") has no `OverdueWindowDays` field yet.

**Independent Test**: Two tenants with different `OverdueWindowDays` (e.g. 7 and 3) see different
due-soon cutoffs for the same days-until-due value; a tenant with no explicit value defaults to 7.

### Tests for FR-012

- [ ] T027 [P] Failing test: a service due in 5 days is `DueSoon` for a tenant with
  `OverdueWindowDays = 7` but not listed at all for a tenant with `OverdueWindowDays = 3`
  (same days-until-due, two tenants) in tests/FleetWise.Tests/DispatcherServiceTests.cs
- [ ] T028 [P] Failing test: `Tenant.OverdueWindowDays` defaults to `7` per data-model.md ("+
  `OverdueWindowDays` (int, default `7`)") when not explicitly set, in
  tests/FleetWise.Tests/DispatcherServiceTests.cs

### Implementation for FR-012

- [ ] T029 Add `OverdueWindowDays` (int, default `7`) to `Tenant` in
  src/FleetWise.Api/Models/Entities.cs, and set it in the seed tenants in
  src/FleetWise.Api/Data/SeedData.cs
- [ ] T030 Replace the hardcoded `DueSoonDays` constant in
  src/FleetWise.Api/Services/DispatcherService.cs with the requesting tenant's
  `OverdueWindowDays` (load the `Tenant` row for `tenantId` in `GetLinesAsync`, per data-model.md's
  rule "days since last service > `IntervalDays - tenant.OverdueWindowDays`")

**Checkpoint**: FR-012 covered; US1's due-soon cutoff is per-tenant everywhere it's read.
