# Application package layout (STORY-CORE-003)

**Story:** STORY-CORE-003 (EPIC-CORE-001).  
**Applies to:** every Frappe app in this monorepo, inner Python package `<app_name>/<app_name>/` (e.g. `kentender/kentender/`).

This document is the canonical reference for **where code lives**. Dependency rules between apps remain in [**App dependencies and boundaries**](app-dependencies-and-boundaries.md).

## Standard folders

| Folder | Purpose |
| ------ | ------- |
| `doctype/` | DocType definitions (JSON + Python controller per DocType). Keep controllers **thin**: field validation, `validate`, hook registration, delegation to `services/`. |
| `services/` | **Business logic and orchestration**: use cases, state transitions, calls that enforce rules. One **snake_case** module per primary concern (e.g. `tender_lifecycle.py`). |
| `api/` | **Whitelisted** HTTP handlers and `@frappe.whitelist()` entry points for `frappe.call`. Thin: parse input, call `services/`, return serializable results—avoid embedding domain rules here. |
| `tests/` | Unit and integration tests: `test_*.py`. Prefer testing `services/` and critical `api/` paths. |
| `utils/` | **Optional pure helpers**: formatting, small algorithms, constants—**no** DocType lifecycle ownership, **no** heavy imports from `services/` (avoid circular imports). |

Frappe also provides `config/`, `public/`, `templates/`, `patches/`, etc.; use those per Frappe conventions.

## Where business logic belongs

1. **DocType controller** — Schema-adjacent behaviour only; call into `services/` for non-trivial rules.
2. **`services/*.py`** — Authoritative place for behaviour described in stories and PRD.
3. **`api/*.py`** — Transport and permission surface; delegate to services.
4. **`utils/`** — Shared within the app when helpers are not service-specific; keep stateless where possible.

## Naming

- Align with [App dependencies and boundaries — Naming](app-dependencies-and-boundaries.md#naming-conventions): DocTypes PascalCase; services **snake_case**; tests `test_*.py`.

### DocType controller Python class (Frappe — non-negotiable)

The Python class in `doctype/<scrub>/<scrub>.py` **must** match Frappe’s loader, not intuitive Title Case:

- **Algorithm:** `doctype.replace(" ", "").replace("-", "")` (see `frappe.model.base_document.import_controller`).
- **Trap:** Titles with words like **“of”, “and”, “for”** often stay lowercase in the desk name, so the class gets a **lowercase letter** where you might expect PascalCase. Example: **Conflict of Interest Declaration** → `ConflictofInterestDeclaration` (lowercase `o`), **not** `ConflictOfInterestDeclaration`.
- **If wrong:** `get_controller` fails with `ImportError`. On **`bench migrate`**, `remove_orphan_doctypes()` treats that as an **orphan DocType** and **deletes the row**, which is painful to debug.
- **Check before merge:** `bench --site <site> console` → `frappe.clear_cache(); from frappe.model.base_document import get_controller; get_controller("Your DocType Name")` must return a class.

Cursor agents: see repo rule **kentender-frappe-doctype-controller-class**.

### Child table (`istable`) validation (Frappe — easy to get wrong)

DocTypes with **`"istable": 1`** are saved as rows of a parent **Table** field. On parent **insert/save**, Frappe runs the parent’s **`validate`**, but on each child row it runs only built-in **`_validate_*`** checks — **not** the child class’s **`validate()`** method. Custom rules on child rows (link checks, derived fields, score ranges) **will not run** unless you invoke them from **`Parent.validate()`** (e.g. loop `self.lines` and call a shared `validate_<child>_row(self, row)`).

Also: during the parent’s **`validate()`** on **first insert**, the parent row may **not exist in the DB yet** — avoid assuming `frappe.get_doc(parenttype, parent.name)` is enough; pass the **in-memory parent document** and resolve links that already exist (e.g. session → tender via `get_value`).

In-repo pattern: **PROC-STORY-062** (`validate_evaluation_score_line_row` from `EvaluationRecord._validate_score_lines`).

Cursor agents: see repo rule **kentender-frappe-child-table-validation**.

## Cross-app interaction

- Do **not** import another app’s `services/` internals. Use whitelisted `api`, documented `frappe.call`, or shared contracts in **`kentender`** as described in the boundaries doc.

## Discoverability

- New features should land in predictable paths above so Cursor and reviewers find them without app-specific one-offs.
- Layout imports are smoke-tested per app in `tests/test_package_layout.py`.

## Related

- [Architecture index](README.md)
- [Wave 0 Ticket Pack — STORY-CORE-003](../dev/Wave%200%20Ticket%20Pack.md)
