# Wave 0 backlog (tracking)

**Purpose:** Sprint and PR tracking only. Do **not** duplicate full objectives, scope, acceptance criteria, tests, or Cursor prompts here.

**Maintenance:** After each merged story (or agreed milestone), update the **Status** and **Notes** columns for that row. Use `Done` only when the ticket’s acceptance criteria in the pack are met.

**Canonical source:** Every Wave 0 story’s full ticket lives in [`Wave 0 Ticket Pack.md`](Wave%200%20Ticket%20Pack.md) under the matching `**STORY-CORE-xxx**` heading.

**Execution order:** Follow the Ticket Pack’s closing list (steps 1–22 below). Do **not** use [`KenTender Master Epic Map.md`](KenTender%20Master%20Epic%20Map.md) §5 for Wave 0 ordering (it can diverge from the pack).

| Story ID | Title (short) | Epic | Depends on | Step # | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| STORY-CORE-001 | Initialize multi-app KenTender workspace | EPIC-CORE-001 | none | 1 | Done | **Monorepo:** git root `apps/kentender_platform/`; nine app subdirs; bench symlinks `apps/<app> → kentender_platform/<app>`. Core app name stays `kentender` (ticket’s kentender_core role). Layout + docs folders + smoke tests; see [`scripts/link_apps_on_bench.sh`](../../scripts/link_apps_on_bench.sh). |
| STORY-CORE-002 | Set app dependency boundaries and shared config conventions | EPIC-CORE-001 | STORY-CORE-001 | 2 | Not Started | |
| STORY-CORE-003 | Create common service module structure across apps | EPIC-CORE-001 | STORY-CORE-001, STORY-CORE-002 | 3 | Not Started | |
| STORY-CORE-004 | Implement Procuring Entity DocType | EPIC-CORE-002 | STORY-CORE-001 | 4 | Not Started | |
| STORY-CORE-005 | Implement Department / Business Unit DocType | EPIC-CORE-002 | STORY-CORE-004 | 5 | Not Started | |
| STORY-CORE-006 | Implement shared master data DocTypes | EPIC-CORE-002 | STORY-CORE-004 | 6 | Not Started | |
| STORY-CORE-007 | Implement naming/number generation service | EPIC-CORE-002 | STORY-CORE-006 | 7 | Not Started | |
| STORY-CORE-015 | Implement Exception Record DocType | EPIC-CORE-005 | STORY-CORE-001 | 8 | Not Started | |
| STORY-CORE-016 | Implement audit event service and event schema | EPIC-CORE-005 | STORY-CORE-001 | 9 | Not Started | |
| STORY-CORE-017 | Implement access-denied and sensitive-access audit hooks | EPIC-CORE-005 | STORY-CORE-016 | 10 | Not Started | |
| STORY-CORE-018 | Implement shared typed attachment model | EPIC-CORE-006 | STORY-CORE-006 | 11 | Not Started | |
| STORY-CORE-019 | Implement sensitivity classification handling | EPIC-CORE-006 | STORY-CORE-018 | 12 | Not Started | |
| STORY-CORE-020 | Implement protected file access service for sensitive documents | EPIC-CORE-006 | STORY-CORE-018, STORY-CORE-019, STORY-CORE-017 | 13 | Not Started | |
| STORY-CORE-008 | Implement entity scope utility layer | EPIC-CORE-003 | STORY-CORE-004, STORY-CORE-005 | 14 | Not Started | |
| STORY-CORE-009 | Implement assignment-based access helper framework | EPIC-CORE-003 | STORY-CORE-003 | 15 | Not Started | |
| STORY-CORE-010 | Implement permission query helper framework | EPIC-CORE-003 | STORY-CORE-008, STORY-CORE-009 | 16 | Not Started | |
| STORY-CORE-011 | Implement separation-of-duty conflict rule DocType and service | EPIC-CORE-003 | STORY-CORE-006, STORY-CORE-003 | 17 | Not Started | |
| STORY-CORE-012 | Implement Workflow Guard Rule DocType | EPIC-CORE-004 | *(not in pack — after step 17)* | 18 | Not Started | |
| STORY-CORE-013 | Implement shared workflow guard service | EPIC-CORE-004 | STORY-CORE-012 | 19 | Not Started | |
| STORY-CORE-014 | Implement controlled business action pattern | EPIC-CORE-004 | STORY-CORE-013, STORY-CORE-016 | 20 | Not Started | |
| STORY-CORE-021 | Implement Notification Template DocType | EPIC-CORE-007 | *(not in pack — after foundation)* | 21 | Not Started | |
| STORY-CORE-022 | Implement notification dispatch service abstraction | EPIC-CORE-007 | STORY-CORE-021 | 22 | Not Started | |

**Depends on:** Values match explicit `**Depends on:**` lines in the Ticket Pack where present. STORY-CORE-012–014 are bundled without per-story dependency lines; STORY-CORE-013/014 rows reflect the bundle’s technical chain (014’s prompt requires audit events → STORY-CORE-016). STORY-CORE-021 has no `**Depends on:**` line in the pack; STORY-CORE-022 follows the template DocType in implementation order.

**Status values:** `Not Started` | `In Progress` | `Blocked` | `Done`

## Wave 1

Wave 1 stories remain described in [`KenTender Master Epic Map.md`](KenTender%20Master%20Epic%20Map.md) §4 until a dedicated Wave 1 ticket pack exists.
