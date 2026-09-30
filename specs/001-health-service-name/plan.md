# Implementation Plan: Health Endpoint Service Name

**Branch**: `demo/delivery-20260930-201143-26d0ce05` | **Date**: 2026-09-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-health-service-name/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Add a fixed `service: "FleetWise.Api"` field to the existing `GET /health` minimal-API response
in `Program.cs`, alongside the unchanged `status: "ok"` field. Extend the existing
`Health_is_ok` xUnit test to assert both fields. No new files, services, or dependencies.

## Technical Context

**Language/Version**: C# / .NET 8

**Primary Dependencies**: ASP.NET Core minimal APIs (`Program.cs` top-level `MapGet`), no new packages

**Storage**: N/A - `/health` is a static literal response, no DB access

**Testing**: xUnit + `Microsoft.AspNetCore.Mvc.Testing` (`WebApplicationFactory`), existing
`ApiTests.Health_is_ok` in `tests/FleetWise.Tests/SeedAndApiTests.cs`

**Target Platform**: Existing FleetWise.Api ASP.NET Core web service

**Project Type**: Single web-service project (`src/FleetWise.Api`) with a companion test project
(`tests/FleetWise.Tests`)

**Performance Goals**: N/A - unchanged from current `/health` (trivial literal response)

**Constraints**: Additive only; `status` field, HTTP 200, anonymous access, and all other
endpoints must stay byte-for-byte unchanged

**Scale/Scope**: One line changed in `Program.cs`, one test extended - no other scope

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Layered Data Access**: N/A - `/health` is a literal response with no data access; no
  `Services/` or `DbContext` involvement to violate.
- **II. Tenant Isolation**: N/A - no query, no `TenantId`, no tenant-scoped data involved.
- **III. Test-First**: Satisfied - plan extends the existing `Health_is_ok` test (the matching
  characterization test) to assert the new field and confirm failure before the implementation change.
- **IV. Backward-Compatible Public API**: Satisfied - change is purely additive (`service` field
  added); `status` field, status code, and all other routes are untouched.
- **V. Configuration and Secrets**: Satisfied - no config, secrets, or time values introduced;
  value is a hardcoded literal per spec Assumptions.

**Result**: PASS, no violations, no Complexity Tracking entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-health-service-name/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/FleetWise.Api/
└── Program.cs               # MapGet("/health", ...) - add `service` field here

tests/FleetWise.Tests/
└── SeedAndApiTests.cs        # ApiTests.Health_is_ok - extend assertions here
```

**Structure Decision**: Existing single ASP.NET Core Web API project
(`src/FleetWise.Api`) plus its xUnit test project (`tests/FleetWise.Tests`). No new
projects, folders, or files are introduced; the change is confined to one existing
minimal-API route and its one existing regression test.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - table intentionally omitted.
