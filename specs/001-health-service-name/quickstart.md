# Quickstart: Validate Health Endpoint Service Name

## Prerequisites

- .NET 8 SDK installed.
- Repository checked out at this feature branch.

## Run the regression test

```bash
dotnet test tests/FleetWise.Tests --filter Health_is_ok
```

**Expected**: Test passes, asserting HTTP 200 and a JSON body with both
`status: "ok"` and `service: "FleetWise.Api"` (see [contracts/health.md](./contracts/health.md)).

## Manual check (optional)

```bash
dotnet run --project src/FleetWise.Api --urls http://localhost:5082
```

In another terminal:

```bash
curl -fsS http://localhost:5082/health
# {"status":"ok","service":"FleetWise.Api"}
```

Stop the API with Ctrl+C when finished.

## Full regression

```bash
dotnet test
```

**Expected**: All existing tests still pass - no endpoint other than `/health` changes.
