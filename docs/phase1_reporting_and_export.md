# Phase 1 reporting and export APIs

This note captures the current API surface for **Phase 1 APP/PR reporting** and lightweight evidence export.

## APIs (whitelisted)

### `phase1_get_reporting_snapshot`

Returns JSON aggregates scoped by optional `company` and `fiscal_year`.

Current payload sections:
- `app_summary` (count, status counts, total budget/committed/actual)
- `plan_item_summary` (budget status distribution, risk level distribution)
- `override_summary` (override counts by type)
- `pr_summary` (PR status/readiness counts, linked tender totals)
- `handoff_rows` (latest `Requisition Tender Handoff` rows)

Example bench call:

`bench --site <site> execute kentender.kentender.api.phase1_get_reporting_snapshot --args "['Midas (Demo)','2025-2026']"`

### `phase1_download_reporting_snapshot_csv`

Returns CSV download for handoff rows (`Requisition Tender Handoff`) in the same scope.

Example API URL:

`/api/method/kentender.kentender.api.phase1_download_reporting_snapshot_csv?company=Midas%20(Demo)&fiscal_year=2025-2026`

## Validation evidence (2026-03-20)

- Snapshot run completed for `company = Midas (Demo)`, `fiscal_year = 2025-2026`.
- Returned live metrics including:
  - APP status counts (`Superseded`, `Locked`, `Draft`)
  - PR readiness (`Fully Handed Off`)
  - handoff row containing `RTH-2026-00054` and `TN-2026-00053`.
- CSV export smoke run generated non-empty file content in response.

## Current limitations

- Outputs are API-first (JSON/CSV). Desk chart widgets and curated report pages are still to be added.
- CSV export currently targets handoff rows; broader evidence-pack assembly can build on this baseline.
