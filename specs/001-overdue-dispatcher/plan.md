# Implementation Plan: Overdue Maintenance Dispatcher

**Branch**: `001-overdue-dispatcher` | **Date**: 2026-09-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-overdue-dispatcher/spec.md`

## Summary

Give fleet managers a dispatcher that lists every vehicle whose scheduled service is overdue or due
within 7 days, suggests a work order with a qualified technician, and books nothing until a
FleetManager approves. Technically: a new `DispatcherService` in the existing service layer computes
due status from `MaintenanceSchedules` and `MaintenanceRecords`, a `DispatchController` exposes it
under `/api/dispatch`, and a new `DispatchDecision` entity records approvals and rejections. The
existing API and the legacy overdue report stay unchanged.

## Technical Context

**Language/Version**: C# 12 / .NET 8

**Primary Dependencies**: ASP.NET Core Web API (controllers), EF Core 8, Swashbuckle

**Storage**: SQLite via EF Core (`EnsureCreated`, no migrations in this codebase)

**Testing**: xUnit, real SQLite in-memory database, deterministic seed, fixed `IClock`

**Target Platform**: Linux or macOS server, local demo

**Project Type**: Web service (existing single API project + test project)

**Performance Goals**: Dispatcher list in under 1 second for a 50-vehicle fleet

**Constraints**: Additive API changes only; tenant resolved per request; no new projects

**Scale/Scope**: 2 tenants, 50 vehicles, 6 schedules in demo data; ~3 endpoints, 2 services

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How this plan complies | Status |
| --- | --- | --- |
| I. Layered Data Access | New logic in `DispatcherService` and `TechnicianMatcher`; `DispatchController` only calls services | PASS |
| II. Tenant Isolation | Tenant read from `X-Tenant-Id` once per request and passed explicitly to `DispatcherService` and `TechnicianMatcher`; vehicle, technician, work-order, and decision queries all filter by `TenantId` | PASS (fixed after `/speckit-analyze` C1) |
| III. Test-First | Each story starts with failing xUnit tests, including a second-tenant test | PASS |
| IV. Backward-Compatible API | New routes under `/api/dispatch` only; existing routes untouched | PASS |
| V. Configuration and Secrets | No secrets; "today" and "next business day" come from `IClock` | PASS |

Post-design re-check: PASS. `/speckit-analyze` found the technician lookup unscoped (C1); fixed here and in
data-model.md so every query in this feature takes `tenantId`.

## Project Structure

### Documentation (this feature)

```text
specs/001-overdue-dispatcher/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── dispatch-api.md
└── tasks.md             # created by /speckit-tasks
```

### Source Code (repository root)

```text
src/FleetWise.Api/
├── Controllers/
│   └── DispatchController.cs        # NEW: /api/dispatch endpoints
├── Models/
│   ├── Entities.cs                  # + DispatchDecision entity, Tenant.DueSoonDays
│   └── Dispatch.cs                  # NEW: DispatchLine, TechnicianSuggestion DTOs
├── Services/
│   ├── DispatcherService.cs         # NEW: due calculation, approve, reject
│   ├── TechnicianMatcher.cs         # NEW: picks a qualified technician
│   └── TenantContext.cs             # NEW: resolves tenant + role from request headers
└── Data/
    └── FleetWiseDbContext.cs        # + DbSet<DispatchDecision>

tests/FleetWise.Tests/
├── DispatcherServiceTests.cs        # NEW: US1 + US3
├── TechnicianMatcherTests.cs        # NEW: US2
└── DispatchApiTests.cs              # NEW: HTTP-level contract tests
```

**Structure Decision**: Extend the existing `FleetWise.Api` and `FleetWise.Tests` projects, following
the controller → service → `DbContext` layering already used by `VehiclesController` and
`WorkOrdersController`.

## Design Notes

- **Due calculation** (per vehicle, per schedule for its vehicle class): distance since the last
  record of that service type and days since it. Overdue when either exceeds the interval; due soon
  when the date falls due within the tenant's due-soon window (`Tenant.DueSoonDays`, default 7,
  FR-012). No history means due now, flagged "no history".
- **Technician suggestion**: `TechnicianMatcher.SuggestAsync(tenantId, requiredSkill)` loads the
  tenant's technicians whose `Skills` include the required skill, then picks the one with the fewest
  scheduled work orders in the next 7 days, ties alphabetical. None qualified means unassigned and
  flagged.
- **Approval**: `POST /api/dispatch/approve` requires `X-User-Role: FleetManager`; creates a
  `Scheduled` work order for the next business day and a `DispatchDecision`. Reject records a
  decision only.
- **Open work orders**: a draft or scheduled work order for the same vehicle and service type marks
  the line as "already handled", with no suggestion.

## Complexity Tracking

No constitution violations to justify.
