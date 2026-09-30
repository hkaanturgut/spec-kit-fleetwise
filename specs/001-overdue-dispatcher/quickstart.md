# Quickstart: validate the dispatcher

## Prerequisites

.NET 8 SDK. From the repository root:

```bash
dotnet test
dotnet run --project src/FleetWise.Api
```

## Scenarios

1. **Tenant-scoped list (US1)**

   ```bash
   curl -s localhost:5080/api/dispatch -H "X-Tenant-Id: 1"
   ```

   Expect only `LSL-*` units, each with a `trigger` and `status`. Repeat with `X-Tenant-Id: 2` and
   expect only `GLT-*` units.

2. **Missing tenant**

   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" localhost:5080/api/dispatch
   ```

   Expect `400`.

3. **Suggestion without a qualified technician (US2)**: with `X-Tenant-Id: 2`, any `DotInspection`
   line shows `noQualifiedTechnician: true` (tenant 2 has no DOT inspector).

4. **Approval (US3)**: approve a line with `X-User-Role: FleetManager` and expect `201`. The line
   then shows `AlreadyHandled`. The same request without the role returns `403`.

See [contracts/dispatch-api.md](./contracts/dispatch-api.md) and [data-model.md](./data-model.md).
