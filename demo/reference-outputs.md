# Reference outputs from the recorded dry run

What each AI step produced in the dry run that created the checkpoint tags. Use them to narrate if a live step drifts, or to compare against Copilot's live output.

## Discovery output (reference answer for Step 2 discovery prompt)

| Convention | Evidence | Breaks |
| --- | --- | --- |
| Layered: controllers -> services -> EF Core DbContext | VehiclesController -> IVehicleService; WorkOrdersController -> IWorkOrderService (Services/Services.cs) | TechniciansController and ReportsController inject FleetWiseDbContext directly |
| Data access through EF Core with AsNoTracking reads | Services/Services.cs | ReportsController loads every vehicle and record into memory |
| Validation via exceptions mapped to HTTP codes (ArgumentException -> 400, InvalidOperationException -> 409) | VehiclesController, WorkOrdersController | WorkOrderService.CreateAsync validates nothing (vehicle existence, tenant, service type) |
| Testing: xUnit, real SQLite in-memory, deterministic seed, fixed clock | tests/FleetWise.Tests/TestSupport.cs | None |
| Time through IClock, never DateTime.Now in logic | Services/Services.cs, SeedData.cs | None |
| Configuration: connection string from appsettings | Program.cs, appsettings.json | None |
| Multi-tenancy: TenantId column on every entity | Models/Entities.cs | No query filters by TenantId anywhere; comment in FleetWiseDbContext confirms |
| Business rules in services | WorkOrderService state transitions | ReportsController hard-codes "overdue = 10,000 km since any service", ignoring MaintenanceSchedules |


## Specification Analysis Report (reference output at s1-05-plan-tasks)

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Constitution | CRITICAL | plan.md (Design Notes), data-model.md (Rules), tasks.md T017 | `TechnicianMatcher.SuggestAsync(serviceType, requiredSkill)` loads technicians by skill with no `TenantId` scope. It can suggest another customer's technician. Violates Principle II (Tenant Isolation) and FR-010. The plan's Constitution Check marks Principle II as PASS, which is incorrect. | Add `tenantId` to the matcher and scope technician and work-order queries by it; update the Constitution Check; regenerate tasks. |
| H1 | Coverage | HIGH | spec.md FR-010, tasks.md T015-T016 | No test proves technicians from other tenants are never suggested. | Add a failing test with a qualified technician in another tenant. |
| M1 | Coverage | MEDIUM | spec.md SC-001 | No task measures list latency. | Accept for the demo slice or add a timing assertion in quickstart. |
| L1 | Terminology | LOW | spec.md vs plan.md | "customer" (spec) and "tenant" (plan) name the same concept. | Note the mapping once in data-model.md. |

**Coverage**: 11 functional requirements, 10 with at least one task (91%). FR-010 is only partly covered (see H1).

**Constitution Alignment Issues**: 1 (C1, Principle II).

**Metrics**: Total requirements 11 · Total tasks 25 · Critical issues 1 · Ambiguity 0 · Duplication 0.

### Next Actions

Resolve C1 before `/speckit-implement`: update plan.md and data-model.md, then rerun `/speckit-tasks` and `/speckit-analyze`.


## Convergence Findings (reference output at s1-06-implement)

| ID | Gap | Severity | Source | Evidence | Action |
|----|-----|----------|--------|----------|--------|
| F1 | partial | MEDIUM | contracts/dispatch-api.md (X-Tenant-Id: "Missing or invalid: 400") | TenantContext accepts any positive integer; GET /api/dispatch with X-Tenant-Id: 999 returns 200 and an empty list | Appended T026 |

Existing unchecked tasks T015-T025 (User Stories 2 and 3, polish) remain open; they are tracked, so no duplicates were appended.

Outcome: tasks_appended (1 task, Phase 7: Convergence). Next: /speckit-implement to complete T015 onward.

## Real Copilot workflow rehearsal (2026-09-30)

The original checkpoint dry run followed the pinned skills but did not invoke
Copilot. A later local rehearsal used Spec Kit 1.0.13 and Copilot CLI 1.0.89 from
`s1-06-implement`, adding FR-012 without changing the historical tags.

- Bare plan/tasks commands returned successfully without updating the design.
  Analyze correctly reported FR-012 as CRITICAL and uncovered.
- With explicit reconciliation inputs, Copilot updated `plan.md`, `research.md`,
  `data-model.md`, `quickstart.md`, and `tasks.md`.
- Added T027-T030: two-tenant window test, default-seven-days test, tenant field
  and seed data, and dispatcher lookup. T001-T014 stayed completed and T026 stayed open.
- Analyze reported **zero CRITICAL findings** and FR-012 coverage. Existing
  medium gaps remained for post-implementation legacy regression and timing
  coverage; these are not evidence that the unfinished stories are implemented.
- Human review corrected a generated assumption: `TenantContext` parses headers;
  it does not load tenant data. The planned lookup belongs in `DispatcherService`.
- Time to the review gate: **363.4 seconds (6m03s)**. This exceeds the five-minute
  workflow slot. Do not promise a full live run fits; use a prepared result or
  the recorded fallback and narrate the real diffs.

Stamps are written only after review approval. A zero exit code alone is not
proof that a changed requirement was incorporated.

Local readiness checks used SDK 8.0.414 with `global.json` unchanged:

| Check | Result |
| --- | --- |
| Baseline on `main` | 15 tests passed; preflight GREEN |
| US1 implementation checkpoint | 24 tests passed |
| Freshly seeded HTTP API | Legacy report: 4 vehicles; tenant 1: 24 vehicles / 38 lines; tenant 2: 15 vehicles |
| Tenant boundary checks | Disjoint vehicle IDs; missing/non-numeric tenant headers return 400 |
| Workflow scenarios | A-F passed, including no stamps before approval |
| Preflight regressions | Version-output pipe handling, active GitHub account, SDK resolution, and test-failure reporting passed |
| README/docs/demo diagrams | All 13 rendered |

The Copilot-generated artifacts and review corrections are preserved on
`rehearsal/local-ready`, separate from the unchanged historical checkpoint tags.
