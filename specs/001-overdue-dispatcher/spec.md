# Feature Specification: Overdue Maintenance Dispatcher

**Feature Branch**: `001-overdue-dispatcher`

**Created**: 2026-09-30

**Status**: Draft

**Input**: User description: "Fleet managers need an overdue-maintenance dispatcher. Show vehicles that are overdue or due within 7 days, by mileage or by date. Suggest a work order for each vehicle with the right service type and a technician who has the required skill. A manager must approve a work order before it is booked."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See what needs service now (Priority: P1)

A fleet manager opens the dispatcher and sees every vehicle in their fleet that is overdue for a
scheduled service, or will be due within the next 7 days, with the service type, how overdue it is
(in days and kilometres), and whether the trigger was mileage or date.

**Why this priority**: Today the ops team relies on a legacy report that uses one fixed rule and
misses most overdue services. Seeing the true list is valuable on its own, even before any
automation.

**Independent Test**: Load a fleet with known service history and confirm the dispatcher lists
exactly the vehicles whose schedules are overdue or due within 7 days, and none of another
customer's vehicles.

**Acceptance Scenarios**:

1. **Given** a vehicle whose oil change interval is 8,000 km and which has driven 9,000 km since
   its last oil change, **When** the manager opens the dispatcher, **Then** the vehicle is listed as
   overdue for an oil change by 1,000 km.
2. **Given** a vehicle whose brake inspection is due by date in 5 days, **When** the manager opens
   the dispatcher, **Then** it is listed as due soon, with 5 days remaining.
3. **Given** two customers with overdue vehicles, **When** a manager from customer A opens the
   dispatcher, **Then** only customer A's vehicles appear.

---

### User Story 2 - Get a suggested work order (Priority: P2)

For each listed vehicle, the dispatcher proposes a work order: the service type from the schedule
and a technician from the same customer who holds the skill that service requires.

**Why this priority**: It turns the list into action and removes manual matching, but it depends on
Story 1.

**Independent Test**: For a listed vehicle, confirm the suggestion names the scheduled service type
and a technician from the same customer who has the required skill.

**Acceptance Scenarios**:

1. **Given** an overdue oil change and a technician with the Mechanic skill in the same customer,
   **When** the manager views the suggestion, **Then** that technician is proposed.
2. **Given** an overdue service and no technician in the customer with the required skill,
   **When** the manager views the suggestion, **Then** the system
   [NEEDS CLARIFICATION: What happens when no technician in the customer has the required skill?
   Leave it unassigned, suggest another customer's technician, or block the suggestion?]

---

### User Story 3 - Approve before anything is booked (Priority: P3)

A suggested work order is only a proposal. Nothing is booked until a manager approves it. The
manager can approve or reject each suggestion.

**Why this priority**: It keeps a human in control of scheduling, which is required before the
dispatcher can be trusted, but the list and suggestions deliver value first.

**Independent Test**: Approve one suggestion and reject another; confirm only the approved one
becomes a scheduled work order.

**Acceptance Scenarios**:

1. **Given** a suggested work order, **When** an authorized manager approves it, **Then** a
   scheduled work order is created for that vehicle, service type, and technician.
2. **Given** a suggested work order, **When** the manager rejects it, **Then** no work order is
   created and the vehicle stays on the dispatcher list.
3. **Given** a user who is not allowed to approve, **When** they try to approve a suggestion,
   **Then** the approval is refused.

---

### Edge Cases

- A vehicle is overdue for two services at once: each service gets its own line and suggestion.
- A vehicle already has an open (draft or scheduled) work order for that service: it is shown as
  already handled, and no duplicate suggestion is made.
- A vehicle has no service history for a scheduled service: it is treated as due from its current
  odometer and is flagged as "no history".
- A vehicle's class has no maintenance schedules: it does not appear.
- The same vehicle is approved twice at the same moment: only one work order is created.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST list, for the manager's own customer only, every vehicle with a scheduled
  service that is overdue or due within 7 days.
- **FR-002**: System MUST decide "due" from the vehicle's maintenance schedule, by distance
  (kilometres since the last service of that type) and by date (days since the last service of
  that type), whichever comes first.
- **FR-003**: System MUST show, per line, the service type, the trigger (distance or date), and how
  far overdue or how soon it is due.
- **FR-004**: System MUST suggest, per line, a work order with the scheduled service type and a
  technician from the same customer who holds the required skill.
- **FR-005**: System MUST NOT suggest a work order when an open work order already exists for the
  same vehicle and service type.
- **FR-006**: System MUST create a scheduled work order only after a manager approves the
  suggestion.
- **FR-007**: Only [NEEDS CLARIFICATION: Who is allowed to approve? Any user of the customer, users
  with a manager role, or a named approver per fleet?] can approve a suggestion.
- **FR-008**: System MUST record who approved or rejected each suggestion, and when.
- **FR-009**: Existing reports and endpoints MUST keep working unchanged.

### Key Entities *(include if feature involves data)*

- **Dispatch line**: one vehicle and one scheduled service that is overdue or due soon, with the
  trigger and the distance or days involved.
- **Work order suggestion**: a proposed work order for a dispatch line (service type, technician),
  with a decision state: proposed, approved, or rejected.
- **Approval decision**: who decided, when, and the outcome.
- Existing: vehicle, maintenance schedule, maintenance record, technician, work order, customer
  (tenant).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A manager can see every overdue or due-soon service for their fleet in under
  10 seconds from opening the dispatcher.
- **SC-002**: The dispatcher finds 100% of services that are overdue by schedule in the demo data,
  compared with the legacy report's single fixed rule.
- **SC-003**: 0 vehicles from other customers ever appear in a manager's dispatcher.
- **SC-004**: 0 work orders are booked without a recorded approval.
- **SC-005**: A manager can go from list to an approved, scheduled work order in under 1 minute.

## Assumptions

- "Due soon" means within 7 days by date; distance is not projected forward, because daily
  mileage is not recorded.
- The existing maintenance schedules are the source of truth for intervals and required skills.
- The customer (tenant) of the current user is known for every request.
- Approving a suggestion schedules the work order for the next business day; changing the date is
  out of scope for this feature.
- The legacy overdue report stays as is; replacing it is a separate feature.
