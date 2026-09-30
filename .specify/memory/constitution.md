# FleetWise Constitution

## Core Principles

### I. Layered Data Access

All data access goes through the service layer (`Services/`). Controllers MUST NOT inject or use
`FleetWiseDbContext` directly; they call services and map results and exceptions to HTTP responses.

- New code MUST follow this pattern without exception.
- Known debt: `TechniciansController` and `ReportsController` currently use `DbContext` directly.
  They are recorded violations, not allowed patterns, and MUST NOT be copied. Any feature that
  touches them SHOULD move their logic into a service.

Rationale: this is how the rest of FleetWise already works, and it keeps business rules testable
without HTTP.

### II. Tenant Isolation (NON-NEGOTIABLE)

Every query and command MUST be scoped by `TenantId`. No endpoint, service method, or report may
read or change another tenant's data.

- The tenant for a request MUST be resolved once per request and passed to services explicitly.
- Tests for any new query or command MUST include a second tenant and prove its data is excluded.
- Existing unscoped reads are known debt; new code MUST NOT depend on them.

Rationale: FleetWise is multi-tenant SaaS. A cross-tenant data leak is the most severe defect the
product can have. This rule is new, agreed by the team at adoption.

### III. Test-First

New behavior starts with failing xUnit tests, then the implementation makes them pass
(red, green, refactor).

- Tests use the real SQLite in-memory database, the deterministic seed, and a fixed `IClock`.
- Changing legacy behavior requires updating the matching `Characterization_` test in the same
  change, so reviewers see the behavior change explicitly.

Rationale: the existing suite already works this way, and characterization tests make brownfield
change safe.

### IV. Backward-Compatible Public API

The REST API under `/api` is used by existing clients. Changes MUST be additive: new endpoints,
new optional fields, new optional query parameters.

- Existing routes, request shapes, and response fields MUST NOT be removed or change meaning.
- A breaking change requires a new route version and a governance amendment first.

Rationale: FleetWise has customers integrated against the current contract.

### V. Configuration and Secrets

No secrets, keys, or connection strings with credentials in source code. Configuration comes from
`appsettings*.json` without secrets, or from environment variables. Time comes from `IClock`, never
from `DateTime.Now` or `DateTime.UtcNow` in business logic.

Rationale: keeps the app deployable to any environment and keeps time-based rules testable.

## Technology Constraints

- .NET 8 Web API with controllers, EF Core, SQLite locally. No new projects or frameworks without
  a plan that justifies them.
- Business rules live in services, not in controllers or the `DbContext`.
- Maintenance rules come from `MaintenanceSchedules` data, not hard-coded thresholds.

## Development Workflow and Quality Gates

- Every feature follows Spec Kit: spec, clarify, plan, tasks, analyze, implement, converge.
- Gate 1: the spec PR is approved by the product owner and the tech lead before planning.
- Gate 2: the plan PR (plan, data model, contracts, tasks, clean `/speckit-analyze`) is approved by
  the tech lead before implementation.
- Gate 3: code PRs reference task IDs, pass `dotnet test`, and are reviewed against the spec.
- A requirement change starts with a spec change, never a code-only change.

## Governance

This constitution supersedes other practices for FleetWise. Amendments are made by pull request,
require tech lead approval (enforced with CODEOWNERS), and must state the version bump and
rationale. Versioning follows semantic versioning: MAJOR for removed or redefined principles,
MINOR for new principles or sections, PATCH for clarifications. Every plan includes a Constitution
Check, and `/speckit-analyze` treats a violated MUST as critical.

**Version**: 1.0.0 | **Ratified**: 2026-09-30 | **Last Amended**: 2026-09-30
