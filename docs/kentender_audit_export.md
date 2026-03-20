# KenTender audit export (P2 #6)

Immutable **`KenTender Audit Event`** rows are written by `log_ken_tender_audit_event` on governed actions. This document describes **export** APIs for external audit and dashboards.

## Permissions

| Call | Requirement |
|------|-------------|
| `contract=<name>` | Read permission on **Contract** `name`. |
| No contract (global) | Read permission on **KenTender Audit Event** (e.g. System Manager, HoP, Accounting Officer, HoF per DocType permissions). |

Contract-scoped export aggregates events whose **reference** is the contract **or** any document listed in `_AUDIT_CONTRACT_SCOPED_DOCTYPES` that links that contract (Payment Entry, PI, certificates, etc.).

## APIs (whitelisted)

### `get_ken_tender_audit_event_report`

JSON report for UI or integration.

**Parameters:**

- `contract` (optional) — scope to contract + related documents.
- `reference_doctype`, `reference_name` (optional) — exact reference filter when not using `contract`.
- `actions` — comma-separated action names (optional).
- `from_datetime`, `to_datetime` — filter `event_timestamp` (optional).
- `limit` (default 500, max 10000), `limit_start` — pagination.

**Returns:** `{ ok, scope, rows, row_count, ... }`.

### `download_ken_tender_audit_events_csv`

Same filter parameters as above (no `limit_start`; `limit` default 5000, max 50000). Sets `frappe.response` for a **UTF-8 CSV** download.

**Example (JS / desk):**

```js
window.open(
  frappe.urllib.get_full_url(
    `/api/method/kentender.kentender.api.download_ken_tender_audit_events_csv?contract=CT-2026-00001&limit=2000`
  )
);
```

## Event shape

Each row includes: `name`, `creation`, `event_timestamp`, `action`, `reference_doctype`, `reference_name`, `actor`, `actor_roles`, `details_json` (JSON string with transition payloads).

## Notes

- Events are **append-only** (validate blocks edits; trash blocked).
- Very large sites: contract scope builds many `(doctype, name)` pairs; exports are **capped** by `limit` / pair limits—narrow with dates or `actions` when possible.
