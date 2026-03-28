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

## Cross-app interaction

- Do **not** import another app’s `services/` internals. Use whitelisted `api`, documented `frappe.call`, or shared contracts in **`kentender`** as described in the boundaries doc.

## Discoverability

- New features should land in predictable paths above so Cursor and reviewers find them without app-specific one-offs.
- Layout imports are smoke-tested per app in `tests/test_package_layout.py`.

## Related

- [Architecture index](README.md)
- [Wave 0 Ticket Pack — STORY-CORE-003](../dev/Wave%200%20Ticket%20Pack.md)
