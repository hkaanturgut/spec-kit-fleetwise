<!--
Sync Impact Report
Version change: unratified template -> 1.0.0 (initial adoption)
Modified principles: five unnamed template slots replaced with:
  I. Service-Layer Data Access
  II. Mandatory Tenant Isolation
  III. Tests First
  IV. Backward-Compatible REST API
  V. External Configuration and No Secrets in Code
Added sections: Known Debt and Adoption; Development and Review
Removed sections: none; placeholder sections populated
Deferred TODOs: none
Scope: constitution only; dependent templates and commands remain unchanged.
Remove this temporary report before committing the constitution.
-->
# FleetWise Constitution

## Core Principles

### I. Service-Layer Data Access

Application queries and commands MUST access data through the service layer.
Controllers MUST delegate to injected services and MUST NOT use `FleetWiseDbContext`
directly. Business rules belong in services; controllers handle HTTP input and output.
This preserves the existing `VehicleService` and `WorkOrderService` pattern.
Database initialization, seed routines, and test setup are infrastructure operations,
not controller access paths.

### II. Mandatory Tenant Isolation

Every application query and command MUST be scoped by `TenantId`. Reads and writes
of tenant-owned data MUST enforce that scope, including ID lookups, related records,
and technician assignments. A supplied entity ID MUST NOT bypass tenant ownership.
Missing or invalid tenant scope MUST NOT fall back to all tenants.

Maintenance schedules are shared reference data; their use MUST NOT broaden access
to tenant-owned records. This is a new rule adopted on 2026-09-30, not a claim that
the legacy application already isolates tenants.

### III. Tests First

New or intentionally changed behavior MUST start with a failing xUnit test.
The failure MUST demonstrate the missing behavior before implementation; the
implementation MUST make that test pass while preserving unrelated behavior.
Tests MUST reuse the existing SQLite in-memory and fixed-clock helpers where applicable.
Tenant-scoped behavior MUST include a test that excludes another tenant's data.

Characterization tests describe current behavior, including debt. They MUST NOT be
silently removed or weakened; an approved behavior change MUST update its affected
characterization tests in the same change.

### IV. Backward-Compatible REST API

Public REST API changes MUST be additive and backward compatible. Existing routes,
HTTP methods, request and response contracts, and documented status semantics MUST
remain compatible. New features MUST NOT silently remove, rename, or repurpose
existing API members. Compatibility MUST be covered by tests for affected contracts.

Legacy cross-tenant access is debt, not a compatibility guarantee. Remediation MUST
explicitly document its tenant-boundary behavior change and preserve other API
contracts; unrelated breaking changes require a constitution amendment first.

### V. External Configuration and No Secrets in Code

Runtime configuration MUST come from environment variables or `appsettings` through
the existing application configuration system. Secrets MUST NOT be embedded in source,
tests, or committed configuration. Committed `appsettings` files MUST contain only
non-secret values; secret values MUST be supplied externally.

## Known Debt and Adoption

- `src/FleetWise.Api/Controllers/TechniciansController.cs` and
  `src/FleetWise.Api/Controllers/ReportsController.cs` access the context directly.
  These are the two existing service-layer violations, not permitted patterns.
- `src/FleetWise.Api/Data/FleetWiseDbContext.cs` has no tenant query filter, and
  existing services and controllers do not enforce tenant scope. This remains
  explicit debt against Principle II.
- Adoption does not implement remediation. New work MUST NOT copy or expand these
  violations. Plans that touch the debt MUST identify it and state the bounded
  remediation or remaining noncompliance; they MUST NOT claim isolation is complete.

## Development and Review

Plans and pull requests MUST check all five principles. Reviewers MUST verify service
boundaries, tenant-scoped reads and writes, failing-test-first evidence, API compatibility,
and external configuration without committed secrets. Applicable tests MUST pass
before merge.

Intentional legacy behavior changes MUST be specified and reviewed explicitly, with
the affected contracts and characterization tests identified. Existing debt MUST stay
visible until its implementation and tests demonstrate compliance.

## Governance

This constitution governs future changes; conflicting legacy code is evidence of debt,
not authority to bypass a principle. Amendments MUST be proposed through a reviewed
pull request that records the rationale, affected principles, and any migration or
compatibility impact. The team MUST approve an amendment before relying on it.

Version changes follow semantic versioning: MAJOR for incompatible principle removals
or redefinitions, MINOR for new principles or materially expanded guidance, and PATCH
for non-semantic clarifications. Amendments MUST update the version and last-amended
date while preserving the original ratification date.

**Version**: 1.0.0 | **Ratified**: 2026-09-30 | **Last Amended**: 2026-09-30
