# Research: Overdue Maintenance Dispatcher

## R1. How is the tenant known for a request?

- **Decision**: Read `X-Tenant-Id` (required) and `X-User-Role` / `X-User-Name` (for approvals) from
  request headers in a small `TenantContext` resolver, once per request.
- **Rationale**: FleetWise has no authentication today. Headers are the smallest additive change
  that lets every new endpoint be tenant-scoped now, and they map one-to-one to claims when real
  authentication arrives.
- **Alternatives considered**: EF Core global query filter on `TenantId` (rejected for this slice:
  it would change the behavior of every existing endpoint at once, which violates Principle IV
  and breaks the characterization tests); a tenant route segment (rejected: changes URL shape).

## R2. Where does "due" come from?

- **Decision**: From `MaintenanceSchedules` (interval in km and days per vehicle class and service
  type) combined with the latest `MaintenanceRecord` of that service type.
- **Rationale**: The constitution requires schedule-driven rules; the legacy report's fixed
  10,000 km rule misses date-based and class-specific intervals.
- **Alternatives considered**: Reusing `ReportsController.Overdue` (rejected: hard-coded rule and
  controller-level data access are recorded debt).

## R3. Projecting distance for "due soon"

- **Decision**: Only date intervals produce "due soon"; distance produces "overdue" only.
- **Rationale**: Daily mileage is not recorded, so a distance projection would be a guess (spec
  assumption).
- **Alternatives considered**: Average km/day from history (deferred: not enough data points).

## R4. Next business day for approved work orders

- **Decision**: The next Monday to Friday date after `IClock.UtcNow`, in UTC.
- **Rationale**: Spec assumption; keeps scheduling deterministic in tests through `IClock`.
- **Alternatives considered**: Manager picks a date (out of scope for this feature).

## R5. Preventing double booking

- **Decision**: Before creating a work order on approval, check for an open (draft or scheduled)
  work order for the same vehicle and service type inside the same save; reject with 409 if found.
- **Rationale**: Covers the "approved twice at the same moment" edge case in a single-instance demo.
- **Alternatives considered**: Unique index (rejected: completed work orders must be allowed to
  repeat).

## R6. Per-tenant due-soon window (FR-012)

- **Decision**: Add `DueSoonDays` (int, default 7, range 1-60) to the existing `Tenant` entity and
  read it once per `GetLinesAsync(tenantId)` call.
- **Rationale**: One additive column on an entity FleetWise already has; no new table, no API
  change for existing clients (Principle IV).
- **Alternatives considered**: `appsettings` per tenant (rejected: not editable per customer);
  per-schedule windows (rejected: not requested).
