# KenTender workspace conventions (UI-STORY-001)

**Owner app:** Workspaces and this note live in the **`kentender`** app until a dedicated `kentender_core` app exists. If `kentender_core` is introduced later, re-home workspace JSON and this document there and update [UAT AND WORKSPACE IMPLEMENTATION BACKLOG](UAT%20AND%20WORKSPACE%20IMPLEMENTATION%20BACKLOG.md) Table A notes.

**Principles**

- **Role-centric UI:** Desk navigation is grouped by persona and process, not by backend app names.
- **Business labels:** Shortcuts use tester-facing names (for example “My Requisitions”) even when the underlying DocType differs.
- **Task-first:** Prefer “New …”, queue reports, and filtered lists over raw master-data dumps.
- **Extend, don’t fork:** Add shortcuts and links as modules ship; avoid duplicating ERPNext/Frappe desk modules.

**Naming**

- Workspace **labels** are prefixed with `KenTender` to avoid collisions with ERPNext workspaces on the same site.
- UAT **Frappe Role** names use the `KT UAT` prefix for clarity and easy filtering.

**Paths**

- Workspace JSON (must sit under the **nested** package so `bench migrate` syncs them): `kentender/kentender/kentender/workspace/<workspace_folder>/<workspace_name>.json`
- UAT bootstrap: `kentender/kentender/uat/bootstrap.py` (import path `kentender.uat.bootstrap`)
