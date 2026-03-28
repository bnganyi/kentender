# KenTender architecture notes

## Bench app names vs Wave 0 ticket

The Wave 0 ticket ([`Wave 0 Ticket Pack.md`](../dev/Wave%200%20Ticket%20Pack.md)) names the foundation app **`kentender_core`**. On this bench, that role is fulfilled by the Frappe app **`kentender`** (`app_name = "kentender"` in hooks). In the **monorepo**, that app’s source lives under **`kentender_platform/kentender/`** in git; on a typical bench it is linked as **`frappe-bench/apps/kentender`** → `kentender_platform/kentender` (symlink). All references to **kentender_core** in epics and stories mean this app until a dedicated rename/migration is executed.

The eight other apps live as **sibling directories** in the same repository (`kentender_strategy/`, …) and should be symlinked or `get-app`’d into `frappe-bench/apps/<app_name>/` the same way.

## KenTender Frappe apps (nine)

| Bench `app_name` | Role (short) |
| ---------------- | ------------ |
| `kentender` | Platform foundation (Wave 0 **kentender_core**); shared services, master data, security primitives |
| `kentender_strategy` | Strategy layer (plans, policies upstream of budget/procurement) |
| `kentender_budget` | Budget backbone |
| `kentender_procurement` | Procurement / tendering lifecycle |
| `kentender_governance` | Governance (committees, approvals overlay) |
| `kentender_compliance` | Compliance checks and reporting hooks |
| `kentender_stores` | Stores and inventory integration |
| `kentender_assets` | Asset management integration |
| `kentender_integrations` | External systems (payments, portals, EDI, etc.) |

Dependency direction and naming conventions are defined further in STORY-CORE-002; STORY-CORE-001 only scaffolded installable apps and common empty layout folders (`doctype/`, `services/`, `api/`, `tests/`).

## Rename to `kentender_core` (deferred)

Renaming **`kentender` → `kentender_core`** changes the app identity in the site database (`installed_apps`, module defs, assets paths). It is **out of scope for STORY-CORE-001**. When you proceed:

1. Back up the site.
2. Uninstall `kentender` / install `kentender_core` (or use an approved Frappe migration path).
3. Update `sites/apps.txt`, CI (`bench get-app` / `install-app` / `run-tests`), hooks, and any hard-coded paths.
4. Re-run migrate and smoke tests.

## Layout convention (per app)

Inside each app’s Python package (`<app_name>/<app_name>/`):

- `doctype/` — DocTypes (empty until stories add them)
- `services/` — business logic modules
- `api/` — HTTP / whitelisted API handlers
- `tests/` — unit tests
