# Research: Health Endpoint Service Name

No `NEEDS CLARIFICATION` markers remained in Technical Context - the spec's Assumptions section
already resolved the one open question (hardcoded literal vs. config-driven value). Nothing else
to research: one existing minimal-API endpoint, one existing test, no new dependency.

- **Decision**: Add `service = "FleetWise.Api"` as a hardcoded literal in the anonymous object
  passed to `Results.Ok(...)` in `Program.cs`.
- **Rationale**: Spec explicitly states the name is fixed, not derived from configuration,
  environment, or assembly metadata - a literal is the direct implementation of that requirement.
- **Alternatives considered**: Reading from `IHostEnvironment.ApplicationName` or `appsettings.json`
  - rejected because the spec rules it out and it would add an indirection with no behavior
  difference today (YAGNI).
