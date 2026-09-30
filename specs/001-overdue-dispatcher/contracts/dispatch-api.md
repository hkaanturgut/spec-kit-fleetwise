# Contract: Dispatch API

All endpoints are new and additive. Every request MUST send `X-Tenant-Id`.

| Header | Required | Meaning |
| --- | --- | --- |
| `X-Tenant-Id` | Always | The customer (tenant) the request acts for. Missing or invalid: `400` |
| `X-User-Role` | Approve, reject | Must be `FleetManager`, otherwise `403` |
| `X-User-Name` | Approve, reject | Recorded as `DecidedBy` |

## GET /api/dispatch

Lists dispatch lines for the tenant, most overdue first.

`200 OK`

```json
{
  "generatedAt": "2026-10-01T12:00:00Z",
  "count": 2,
  "lines": [
    {
      "vehicleId": 4,
      "unitNumber": "LSL-004",
      "serviceType": "OilChange",
      "status": "Overdue",
      "trigger": "Distance",
      "kmOverdue": 1200,
      "daysUntilDue": 12,
      "suggestion": { "technicianId": 2, "technicianName": "Dave Chen", "noQualifiedTechnician": false }
    }
  ]
}
```

## POST /api/dispatch/approve

```json
{ "vehicleId": 4, "serviceType": "OilChange", "technicianId": 2 }
```

| Result | When |
| --- | --- |
| `201 Created` + work order | Line exists for the tenant; work order scheduled for the next business day |
| `400` | Missing `X-Tenant-Id` |
| `403` | Role is not `FleetManager` |
| `404` | Vehicle not in this tenant, or no dispatch line for that service |
| `409` | An open work order already exists for the vehicle and service |

## POST /api/dispatch/reject

```json
{ "vehicleId": 4, "serviceType": "OilChange" }
```

| Result | When |
| --- | --- |
| `204 No Content` | Decision recorded; vehicle stays on the list |
| `400` / `403` / `404` | As for approve |
