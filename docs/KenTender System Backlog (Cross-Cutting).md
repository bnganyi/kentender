# KenTender System Backlog (Cross-Cutting)

System-wide items that span phases (not owned by a single module doc).  
**Status:** backlog — to be scheduled and broken into sprints when you pick them up.

---

## UX: Forms, child tables, and list views (entire system)

**Scope:** Apply the same design discipline used for **Purchase Requisition** (tabs, sections, balanced layout, grid columns) across KenTender and integrated ERPNext/HRMS surfaces where we own or customize the DocType.

| # | Item | Notes |
|---|------|--------|
| B-UX-01 | **Form layout pass (Desk)** | Tab/section patterns for Phase 2+ DocTypes (`Tender`, `Tender Submission`, `Award Decision`, supplier governance, CLM where still flat). Align with workflow order (read → act → approve → audit). |
| B-UX-02 | **Child table grid defaults** | Ensure `in_list_view` (and reasonable column count) on all KenTender **child tables** so grids are informative without opening each row. |
| B-UX-03 | **Parent list views from menus** | Standardize **List** settings: default filters, columns (`in_list_view` on parent DocTypes), saved views where helpful, consistent sort for operational queues (e.g. “my pending”, “by status”). |
| B-UX-04 | **Workspace / sidebar consistency** | Keep hub sidebars aligned with form tabs and list queues; avoid duplicate links; same-tab navigation patterns. |
| B-UX-05 | **Design handoff (e.g. Stitch → Frappe)** | Use external layout tools for **prototypes** only; record target layout in a short spec per DocType before implementing Custom Fields / Property Setters / client scripts. |

**Reference implementation:** `docs/technical/purchase-requisition-desk-ux.md` and `phase1_setup_purchase_requisition_form_layout()` in `kentender/kentender/api.py`.

---

## Security & UX: Role-based field visibility (entire system)

**Goal:** Hide or read-only **sensitive or irrelevant** fields by **role**, using Frappe-native mechanisms first (no brittle client-only hiding for security-sensitive data).

| # | Item | Notes |
|---|------|--------|
| B-SEC-01 | **`permlevel` design standard** | Define a small set of levels (e.g. `0` default, `1` procurement ops, `2` approvers/audit, `9` system) and a mapping document per DocType. |
| B-SEC-02 | **Role permissions × permlevel** | Assign **Role** permissions on DocType/DocField so supplier users, requestors, evaluators, auditors, etc. only see fields appropriate to SoD. Prefer **Role Permissions Manager** + exported fixtures where stable. |
| B-SEC-03 | **Child table field permlevels** | Mirror parent rules on child DocTypes (e.g. approval comments, tender commercial fields, audit timestamps). |
| B-SEC-04 | **List vs form** | Confirm list columns do not expose fields above the user’s permlevel (Frappe usually respects this when list fields are chosen correctly). |
| B-SEC-05 | **Server enforcement unchanged** | Field hiding is **not** a substitute for `validate` / permission checks; all gates remain in hooks and APIs. |

**Frappe primitives (preferred order):** DocField `permlevel` → Role Permission on DocType (level-based read/write) → optional `depends_on` for UX-only progressive disclosure (non-security).

---

## How to use this doc

- When starting a phase or module hardening pass, **pull items** from here into that phase’s technical doc and traceability matrix.
- When an item is delivered, **move it** to the relevant technical reference + UAT evidence, and strike or remove it here (or mark **Done** with date).

---

*Recorded from product direction: extend PR-style UX to the whole system; enforce field visibility with **role permissions** and **permlevels**.*
