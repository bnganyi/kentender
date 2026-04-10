# Wave 6 backlog (tracking)

**Purpose:** Sprint and PR tracking only. Do **not** duplicate full objectives, scope, acceptance criteria, tests, or Cursor prompts here.

**Maintenance:** After each merged story (or agreed milestone), update the **Status** and **Notes** columns for that row. Use `Done` only when the ticket’s acceptance criteria in the pack are met.

**Canonical source:** Every Wave 6 story’s full ticket lives in [`Wave 6 Ticket Pack.md`](../prompts/Wave%206%20Ticket%20Pack.md) under the matching `**OPS-STORY-xxx**` or `**GOV-STORY-xxx**` heading.

**Execution order:** Follow the pack’s **Recommended Wave 6 Build Order** (same sequence as **Step #** below): **Stores** **OPS-001–012**, **Assets** **OPS-013–021**, **Audit & Oversight** **GOV-026–032**, **Transparency & Reporting** **GOV-033–039**.

**Upstream:** Wave 5 complete for the target environment ([`WAVE 5 BACKLOG.md`](WAVE%205%20BACKLOG.md) — inspection **PROC-100–116**, deliberations **GOV-001–011**, complaints **GOV-012–025**). Stores and assets flows assume **Procurement Contract**, **inspection / acceptance**, and **complaints** integration points exist where the pack links them.

**App mapping (repo vs pack wording):** The ticket pack often names a single **`kentender_operations`** app. On this bench, implementation is split per [`app-dependencies-and-boundaries.md`](../architecture/app-dependencies-and-boundaries.md):

- **EPIC-OPS-001 (Stores)** → **`kentender_stores`** — nested module layout under `kentender_stores/kentender_stores/kentender_stores/` (same pattern as procurement/governance).
- **EPIC-OPS-002 (Assets)** → **`kentender_assets`** — same nested layout under `kentender_assets/kentender_assets/kentender_assets/`.
- **EPIC-GOV-003 / EPIC-GOV-004** → **`kentender_governance`** — extend existing governance app; do not duplicate Wave 5 complaint/deliberation DocTypes.

**Cross-app:** Respect the KenTender DAG: `kentender_stores` and `kentender_assets` depend on **`kentender` only** among KenTender apps; integrate with procurement/inspection via **`api/`**, documented **`frappe.call`** contracts, or shared facades in **`kentender`** — no direct imports of other apps’ `services/` internals.

**Tests:** `bench run-tests --app kentender_stores`, `bench run-tests --app kentender_assets`, `bench run-tests --app kentender_governance` (and any other app a story touches); keep green per story.

**Minimal Golden UAT:** Extend canonical JSON / loaders / `verify_minimal_golden` when a story needs deterministic rows; otherwise note skip in **Notes**. Follow [`uat/seed_packs/minimal_golden/README.md`](../../uat/seed_packs/minimal_golden/README.md).

**Parallel UI / UAT:** Workspaces and acceptance journeys remain in [`UAT AND WORKSPACE IMPLEMENTATION BACKLOG.md`](../testing/UAT%20AND%20WORKSPACE%20IMPLEMENTATION%20BACKLOG.md) unless this backlog explicitly adds desk links.

| Story ID | Title (short) | Epic | Depends on (pack) | Step # | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| OPS-STORY-001 | Store | EPIC-OPS-001 | — | 1 | Done | [`store`](../../kentender_stores/kentender_stores/kentender_stores/doctype/store/) (`autoname` `field:store_code`, `display_label`; Central/Project/Department); [`test_store_doctypes_001_002.py`](../../kentender_stores/kentender_stores/tests/test_store_doctypes_001_002.py). |
| OPS-STORY-002 | Store Item | EPIC-OPS-001 | OPS-STORY-001 | 2 | Done | [`store_item`](../../kentender_stores/kentender_stores/kentender_stores/doctype/store_item/) (`hash` autoname; unique `store` + `item_code`); [`test_store_doctypes_001_002.py`](../../kentender_stores/kentender_stores/tests/test_store_doctypes_001_002.py). |
| OPS-STORY-003 | Goods Receipt Note (GRN) | EPIC-OPS-001 | OPS-STORY-001; contract / inspection refs (pack) | 3 | Done | [`goods_receipt_note`](../../kentender_stores/kentender_stores/kentender_stores/doctype/goods_receipt_note/) (`field:business_id`; links **Procurement Contract**, **Store**, optional **Inspection Record** / **Acceptance Record**; line totals only — no stock); [`test_grn_doctypes_003_004.py`](../../kentender_stores/kentender_stores/tests/test_grn_doctypes_003_004.py). |
| OPS-STORY-004 | GRN Line | EPIC-OPS-001 | OPS-STORY-003 | 4 | Done | [`grn_line`](../../kentender_stores/kentender_stores/kentender_stores/doctype/grn_line/) (child **Table** `items` on **Goods Receipt Note**); [`test_grn_doctypes_003_004.py`](../../kentender_stores/kentender_stores/tests/test_grn_doctypes_003_004.py). |
| OPS-STORY-005 | Store Ledger Entry | EPIC-OPS-001 | OPS-STORY-001 | 5 | Done | [`store_ledger_entry`](../../kentender_stores/kentender_stores/kentender_stores/doctype/store_ledger_entry/) (`hash` autoname; append-only + `entry_hash`; optional delete via `allow_store_ledger_delete`); [`test_store_chain_005_008.py`](../../kentender_stores/kentender_stores/tests/test_store_chain_005_008.py). |
| OPS-STORY-006 | Stock Movement | EPIC-OPS-001 | OPS-STORY-005 (pack chain) | 6 | Done | [`stock_movement`](../../kentender_stores/kentender_stores/kentender_stores/doctype/stock_movement/) + [`stock_movement_line`](../../kentender_stores/kentender_stores/kentender_stores/doctype/stock_movement_line/) (`field:business_id`; from/to store, lines); [`test_store_chain_005_008.py`](../../kentender_stores/kentender_stores/tests/test_store_chain_005_008.py). |
| OPS-STORY-007 | Store Issue | EPIC-OPS-001 | OPS-STORY-006 / store chain | 7 | Done | [`store_issue`](../../kentender_stores/kentender_stores/kentender_stores/doctype/store_issue/) + [`store_issue_line`](../../kentender_stores/kentender_stores/kentender_stores/doctype/store_issue_line/); [`test_store_chain_005_008.py`](../../kentender_stores/kentender_stores/tests/test_store_chain_005_008.py). |
| OPS-STORY-008 | Store Reconciliation Record | EPIC-OPS-001 | OPS-STORY-005+ | 8 | Done | [`store_reconciliation_record`](../../kentender_stores/kentender_stores/kentender_stores/doctype/store_reconciliation_record/) + [`store_reconciliation_line`](../../kentender_stores/kentender_stores/kentender_stores/doctype/store_reconciliation_line/) (book vs counted; line `variance_quantity`); [`test_store_chain_005_008.py`](../../kentender_stores/kentender_stores/tests/test_store_chain_005_008.py). |
| OPS-STORY-009 | receive goods from contract service | EPIC-OPS-001 | OPS-STORY-003–005; acceptance / contract (pack) | 9 | Done | [`receive_goods_from_contract`](../../kentender_stores/kentender_stores/services/receive_goods_from_contract.py) (`receive_goods_from_contract_api` whitelisted); GRN status **Received** + inbound **Store Ledger**; **Procurement Contract** `completion_percent` bump; [`test_receive_goods_from_contract_009.py`](../../kentender_stores/kentender_stores/tests/test_receive_goods_from_contract_009.py). |
| OPS-STORY-010 | stock issue/transfer services | EPIC-OPS-001 | OPS-STORY-006–007 | 10 | Done | [`stock_issue_transfer_services`](../../kentender_stores/kentender_stores/services/stock_issue_transfer_services.py) (`transfer_stock_between_stores` / `issue_stock_from_store`; whitelisted `*_api`); **Stock Movement** → **Completed** + paired Transfer **In**/**Out** SLE; **Store Issue** → **Issued** + Issue **Out** SLE; [`test_stock_issue_transfer_010.py`](../../kentender_stores/kentender_stores/tests/test_stock_issue_transfer_010.py). |
| OPS-STORY-011 | store ledger integration and balance computation | EPIC-OPS-001 | OPS-STORY-005 | 11 | Not Started | — |
| OPS-STORY-012 | store queue/report scaffolding | EPIC-OPS-001 | Stores chain | 12 | Not Started | — |
| OPS-STORY-013 | Asset | EPIC-OPS-002 | — | 13 | Not Started | — |
| OPS-STORY-014 | Asset Category | EPIC-OPS-002 | OPS-STORY-013 | 14 | Not Started | — |
| OPS-STORY-015 | Asset Assignment | EPIC-OPS-002 | OPS-STORY-013 | 15 | Not Started | — |
| OPS-STORY-016 | Asset Condition Log | EPIC-OPS-002 | OPS-STORY-013 | 16 | Not Started | — |
| OPS-STORY-017 | Asset Maintenance Record | EPIC-OPS-002 | OPS-STORY-013 | 17 | Not Started | — |
| OPS-STORY-018 | Asset Disposal Record | EPIC-OPS-002 | OPS-STORY-013 | 18 | Not Started | — |
| OPS-STORY-019 | create asset from GRN/contract service | EPIC-OPS-002 | OPS-STORY-003; OPS-STORY-013 | 19 | Not Started | — |
| OPS-STORY-020 | asset lifecycle services | EPIC-OPS-002 | OPS-STORY-013–018 (subset per pack) | 20 | Not Started | — |
| OPS-STORY-021 | asset reporting and tracking scaffolding | EPIC-OPS-002 | Assets chain | 21 | Not Started | — |
| GOV-STORY-026 | Audit Query | EPIC-GOV-003 | — | 22 | Not Started | — |
| GOV-STORY-027 | Audit Finding | EPIC-GOV-003 | GOV-STORY-026 | 23 | Not Started | — |
| GOV-STORY-028 | Audit Response | EPIC-GOV-003 | GOV-STORY-026 | 24 | Not Started | — |
| GOV-STORY-029 | Audit Action Tracking | EPIC-GOV-003 | GOV-STORY-027–028 (pack) | 25 | Not Started | — |
| GOV-STORY-030 | cross-module trace service | EPIC-GOV-003 | Known linkages across modules (pack) | 26 | Not Started | — |
| GOV-STORY-031 | audit query/response services | EPIC-GOV-003 | GOV-STORY-026–029 (subset per pack) | 27 | Not Started | — |
| GOV-STORY-032 | audit reporting scaffolding | EPIC-GOV-003 | Audit chain | 28 | Not Started | — |
| GOV-STORY-033 | Public Disclosure Record | EPIC-GOV-004 | — | 29 | Not Started | — |
| GOV-STORY-034 | Disclosure Dataset | EPIC-GOV-004 | GOV-STORY-033 | 30 | Not Started | — |
| GOV-STORY-035 | Report Definition | EPIC-GOV-004 | — | 31 | Not Started | — |
| GOV-STORY-036 | Report Execution Log | EPIC-GOV-004 | GOV-STORY-035 | 32 | Not Started | — |
| GOV-STORY-037 | disclosure generation services | EPIC-GOV-004 | GOV-STORY-033–034 (subset per pack) | 33 | Not Started | — |
| GOV-STORY-038 | reporting/export services | EPIC-GOV-004 | GOV-STORY-035–036 | 34 | Not Started | — |
| GOV-STORY-039 | transparency dashboards (lightweight) | EPIC-GOV-004 | Transparency chain | 35 | Not Started | — |

**Depends on:** Values summarize the Ticket Pack and narrative chain; tighten **Notes** with real paths when stories land.

**Status values:** `Not Started` | `In Progress` | `Blocked` | `Done`

## Design anchor (from pack)

Wave 6 aligns **Budget Ledger Entry** (money), **Store Ledger Entry** (stock), and **contract / inspection** events (delivery) into one accountability story: *Money → Goods → Assets → Outcomes*. See the **Critical Design Insight** section in [`Wave 6 Ticket Pack.md`](../prompts/Wave%206%20Ticket%20Pack.md).

## Related workflow / cross-wave items

If workflow IDs are added for stores, assets, audit, or disclosure, wire **Frappe Workflow** so engine transitions do not bypass service-layer guards ([`WF Implementation Tracker`](../workflow/WF%20Implementation%20Tracker.md)).

## Wave 7+

Not tracked here. See [`KenTender Master Epic Map.md`](../KenTender%20Master%20Epic%20Map.md) until a dedicated Wave 7 backlog exists.
