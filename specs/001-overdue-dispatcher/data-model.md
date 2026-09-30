# Data Model: Overdue Maintenance Dispatcher

## New entity: DispatchDecision (persisted)

Records every approval or rejection (FR-008).

| Field | Type | Rules |
| --- | --- | --- |
| Id | int | Key |
| TenantId | int | Required; always the requesting tenant |
| VehicleId | int | Required; vehicle must belong to TenantId |
| ServiceType | string | Required; must be a schedule service type for the vehicle's class |
| Outcome | enum `Approved` \| `Rejected` | Required |
| TechnicianId | int? | Set on approval when a technician was suggested |
| WorkOrderId | int? | Set on approval to the created work order |
| DecidedBy | string | Required; from `X-User-Name` |
| DecidedOn | DateTime (UTC) | From `IClock` |

## Read models (computed, not persisted)

### DispatchLine

| Field | Type | Meaning |
| --- | --- | --- |
| VehicleId, UnitNumber | int, string | The vehicle |
| ServiceType | string | From the schedule |
| Status | `Overdue` \| `DueSoon` \| `AlreadyHandled` | See state rules below |
| Trigger | `Distance` \| `Date` \| `NoHistory` | What made it due |
| KmOverdue | int? | Positive when past the distance interval |
| DaysUntilDue | int | Negative when overdue by date |
| Suggestion | TechnicianSuggestion? | Null when `AlreadyHandled` |

### TechnicianSuggestion

| Field | Type | Meaning |
| --- | --- | --- |
| TechnicianId | int? | Null when nobody qualifies |
| TechnicianName | string? | |
| NoQualifiedTechnician | bool | FR-010 flag |

## Rules

- A line exists for each (vehicle, schedule) pair where distance since last service > `IntervalKm`,
  or days since last service > `IntervalDays - 7`.
- `AlreadyHandled` when a `Draft` or `Scheduled` work order exists for the same vehicle and service
  type (FR-005).
- Technician selection: `TechnicianMatcher.SuggestAsync(serviceType, requiredSkill)` returns the
  technician holding `requiredSkill` with the fewest `Scheduled` work orders in the next 7 days,
  ties by name (FR-011).

## Existing entities touched

- `WorkOrder`: created with `Status = Scheduled`, `ScheduledFor = next business day` on approval.
  No schema change.
- `FleetWiseDbContext`: adds `DbSet<DispatchDecision>`; `Outcome` stored as string like
  `WorkOrder.Status`.
