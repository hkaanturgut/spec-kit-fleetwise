# Contract: GET /health

**Route**: `GET /health`
**Auth**: Anonymous (unchanged)

## Response - 200 OK

```json
{
  "status": "ok",
  "service": "FleetWise.Api"
}
```

| Field     | Type   | Value                | Notes                                   |
|-----------|--------|-----------------------|------------------------------------------|
| `status`  | string | `"ok"`                | Existing field, unchanged                |
| `service` | string | `"FleetWise.Api"`     | New field, fixed literal, additive only  |

## Compatibility

- Additive change only - existing consumers reading `status` are unaffected.
- No other route, schema, or status code changes.
