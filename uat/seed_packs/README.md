# KenTender UAT seed packs

Deterministic scenario data for QA/UAT and developer milestones. Load via `bench execute` (see [uat/README.md](../README.md)).

## Layout

| Path | Purpose |
|------|---------|
| `mvp_canonical.json` | Single source of truth for **MVP through PR** stable IDs (BASE-REF/STRAT/BUD + SP1). A **bundled copy** ships in the app at `kentender/kentender/uat/mvp/data/mvp_canonical.json` for `bench` installs — edit both when changing IDs. |
| [`minimal_golden/`](minimal_golden/README.md) | **Minimal Golden Scenario** (MOH / `PR-MOH-0001` / workbook IDs). Bundled JSON: `kentender/kentender/uat/minimal_golden/data/minimal_golden_canonical.json`. Loaders: `kentender.uat.minimal_golden`. |
| `base_ref/` | Reserved for optional split BASE-REF fixture files (CSV/JSON) when packs grow. |
| `base_strat/` | Reserved for BASE-STRAT fragments. |
| `base_bud/` | Reserved for BASE-BUD fragments. |
| `sp1_requisition/` | Reserved for SP1-only overrides. |
| `sp2_planning/` | Future: procurement planning (post-MVP milestone). |
| `sp3_tender_bids/` | Future: tender/bids (post-MVP milestone). |

## Conventions

- **Business IDs** for MVP rows use prefix `UAT-MVP` (filter-friendly, human-visible in Desk). Minimal Golden uses workbook IDs (e.g. `MOH`, `PR-MOH-0001`).
- **Idempotency:** loaders upsert by `business_id` (or natural key); `reset_uat_mvp` removes MVP-tagged rows before a clean reload when needed.
- **Commands:** implemented in app package `kentender.uat.mvp` (not in this folder).
