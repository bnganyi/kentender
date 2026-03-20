# Purchase Requisition — Desk form UX (KenTender)

## Goals

- Reduce cognitive load on long mixed stock + custom field layouts.
- Group KenTender governance fields into **tabs** aligned with real workflow order.
- Add **progressive disclosure** for exception-style flags.
- Provide a short **context intro** on the form (Desk).

## What was implemented

### 1) Layout engine (migrate-time)

`phase1_setup_purchase_requisition_form_layout()` in `kentender/kentender/api.py` runs from `phase1_after_migrate_setup()`.

It:

- Inserts **Custom Fields** of type `Tab Break` and `Section Break` (names prefixed with `kentender_` to avoid collisions). Legacy **Column Break** rows (`kentender_col_pr_left` / `kentender_col_pr_right`) are removed on migrate so the form does not look lopsided.
- Rewrites `insert_after` on KenTender **Custom Fields** so the chain is:

  1. **Request classification** (optional): single full-width column after `department` (when present): `entity`, `requestor`, `financial_year`, `requisition_type`, `source_mode`, `required_by_date`.
  2. **Request summary**: section break after `required_by_date`, then **Property Setters** (when those core fields exist) move `requested_by` / `request_by` and `estimated_cost` (or first matching total field) to follow that section so they render full-width instead of continuing a narrow right column.
  3. **Budget & APP linkage** tab after a sensible stock anchor (prefers `estimated_cost`, then other totals / schedule fields, then narrative fallbacks).
  4. **Line items** tab before the custom `items` child table.
  5. **Approvals & workflow** tab before `approvals` / `approval_status`.
  6. **Tender readiness & record audit** tab before tender/audit timestamps.

- Sets `depends_on` on governance flags:
  - `emergency_flag` → `requisition_type == Emergency`
  - `one_off_flag` → `source_mode == One-Off`
  - `exception_flag` → `one_off_flag` checked

### Child table grid columns

`Purchase Requisition Item` and `Purchase Requisition Approval` use `in_list_view` on key fields so the Desk grid shows APP line, description, qty, UOM, line total, status (items) and stage, role, user, action, date (approvals) without opening every row.

### 2) Desk client script

`kentender/public/js/purchase_requisition.js` (wired via `doctype_js` in `hooks.py`) adds a short `frm.set_intro(...)` hint and conditional bullets for One-Off / Emergency.

### 3) New install field chain fix

`required_by_date` custom field now defaults `insert_after` = `source_mode` (avoids two fields stacking on `request_date` on fresh installs).

## Operations

After pulling changes:

```bash
bench --site <site> migrate
bench build --app kentender   # ensures doctype JS is bundled
bench --site <site> clear-cache
```

## Design tools (e.g. Google Stitch)

Use external layout tools to **prototype** tab order and copy; this implementation is the **Frappe translation** (Custom Field geometry + `depends_on` + light client script). Stitch does not deploy into Frappe directly.

## Extension ideas

- Collapsible **Section Break** for audit-only fields (`collapsible_depends_on`).
- Role-based read-only for approval/tender tabs via `permlevel` on Custom Fields.
- Dedicated “Summary” dashboard section using `frm.dashboard`.
