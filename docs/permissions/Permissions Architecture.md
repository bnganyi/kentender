# KenTender permissions architecture

Developer-facing map of how access control is layered in KenTender, aligned with [Roles and Permissions Guidance](Roles%20and%20Permissions%20Guidance.md) (especially §§5–7), [Permission Defect Triage Checklist](KenTender%20Permission%20Defect%20Triage%20Checklist.md), and the [Cursor Implementation Pack](KenTender%20Permissions%20Cursor%20Implementation%20Pack.md).

## Layers and Frappe mechanisms

| Triage layer | Meaning | Primary mechanisms in this codebase |
|--------------|---------|-------------------------------------|
| **A — Workspace / menu** | User sees (or not) a desk entry, shortcut, or workspace card | [Workspace](https://frappeframework.com/docs/user/en/desk/workspace) `roles` on workspace JSON under `kentender/kentender/workspace/` |
| **B — Report open-access** | User can open the report document without “You don’t have access to Report…” | Report child table **Has Role** (from report `*.json`), plus `has_permission(ref_doctype, "report")` on the reference DocType |
| **C — Row-level filtering** | After open, rows match business scope (entity, department, assignment, workflow) | Backend query helpers: `kentender.services.permission_query_service`, `kentender.services.entity_scope_service`, domain services (e.g. `requisition_queue_queries`) |
| **D — DocType baseline** | User can open a DocType form / list at all | DocType **Role Permissions** in JSON or Role Permissions Manager |
| **E — Workflow / controlled actions** | User can submit, approve, publish, etc. | `kentender.services.controlled_action_service.run_controlled_action_gate`, workflow guard rules, DocType `submit`/`write` as appropriate |
| **F — Assignment** | Access only when assigned to a committee / session / case | `kentender.services.assignment_access_service` + **KenTender Assignment** |
| **G — Sensitivity / sealed** | Content or files restricted by classification | `kentender.services.protected_file_access_service`, `kentender.services.sensitivity_classification` |

## What belongs in Role Permissions Manager vs services

- **Use RMP / DocType JSON** for stable baselines: which roles may read, create, write, submit on each DocType. Keep these aligned with Guidance §3 matrices.
- **Do not** rely on RMP alone for “which rows” or “who may approve this step”; that belongs in **services** (scope helpers, controlled actions, assignment checks).
- **Reports** need both: **Layer B** (who may run the report) and **Layer C** (the `execute` path must apply the same scope rules as list APIs).

## Package layout (`kentender.permissions`)

Shared vocabulary and integration points live under `kentender.permissions` (not a separate `kentender_core` app):

- `registry` — stable **business role** keys and **MATRIX_ROLE** Frappe `Role.name` strings (plain labels from the security matrix); helpers such as `user_has_any_matrix_role` (and deprecated `user_has_any_uat_role`).
- `scope` — thin re-exports and small **cross-domain** filter builders that compose `permission_query_service` patterns.
- `reports` — helpers to reason about report access (e.g. `user_can_open_script_report`).
- `actions` — documentation and thin entry points around **PERM-005**; implementation remains in `controlled_action_service`.

Domain-specific row rules (e.g. Purchase Requisition queues) stay in the owning app (`kentender_procurement`) but should call `merge_entity_scope_filters` and `kentender.permissions.registry` for role detection.

## Story-driven permission updates (progressive delivery)

Baseline and row-level permissions are **not** expected to match [Roles and Permissions Guidance](Roles%20and%20Permissions%20Guidance.md) in one upfront sweep. Tighten access **with the user story** (or the relevant PERM story) that introduces or hardens a surface.

**Checklist for each story that adds or materially changes a DocType, report, workspace, or queue**

1. **Matrix** — Identify the §3 / §4 rows that apply; note **X**, **RO**, **RO/F**, **C/R/W/S/A**, etc.
2. **Layer D** — Update DocType `permissions` in JSON (or a focused patch) so Frappe roles match the matrix for that DocType.
3. **Layers A–B** — Adjust workspace `roles` and report **Has Role** rows when the story exposes new desk or report entry points.
4. **Layers C–E** — If the matrix needs **F** (filtered), assignment, or workflow-only actions, extend the appropriate service or `has_permission` in the **same** delivery; JSON alone is not enough for row-level or transition rules.
5. **Migrate** — Run `bench migrate` after JSON permission changes so `tabCustom DocPerm` / report roles update.
6. **Smoke** — Manually verify as at least one non–System Manager persona affected by the change.
7. **Tests (when risk is high)** — In the same PR, add a focused check (e.g. `frappe.has_permission`, or assert save/submit denied for the wrong role) for cross-role mistakes that would be costly.

**Trackers** — After merge, update [PERM Implementation Tracker](PERM%20Implementation%20Tracker.md) and [Matrix audit tracking](Matrix%20audit%20tracking.md) for any row whose status changed (e.g. Partial → tighter note, or Done for a slice).

**Explicit deferral** — Broad alignment of planning DocTypes (e.g. Procurement Plan / Item vs §3B Requisitioner **X**) ships with **PERM-009** or a dedicated planning-permissions story, not as a silent prerequisite for unrelated work.

## References

- [PERM Implementation Tracker](PERM%20Implementation%20Tracker.md) — status of PERM-001–015 from the Cursor Implementation Pack.
- [WF Implementation Tracker](../workflow/WF%20Implementation%20Tracker.md) — status of WF-001–016 (approval workflow engine vs permissions layers).
- Frappe report permission path: `frappe.desk.query_report.get_report_doc` → `Report.is_permitted()` (Has Role) then `has_permission(ref_doctype, "report")`.
- After changing report `roles` in JSON, run **`bench migrate`** so `tabHas Role` for the Report updates.
