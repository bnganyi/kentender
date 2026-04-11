# Implementation audit vs `KenTender_Permissions_Matrix.xlsx`

**Source workbook:** [`KenTender_Permissions_Matrix.xlsx`](KenTender_Permissions_Matrix.xlsx) (sheet **Permissions Matrix**), aligned with **Role Catalogue** and **Legend & Logic** sheets.

**What was done (2026-04-11 — strategy matrix revision):**

1. **New Frappe roles (Strategy & Alignment)** — added to [`kentender/permissions/registry.py`](../../kentender/kentender/permissions/registry.py) as `MATRIX_ROLE` / `BUSINESS_ROLE` and auto-created by [`kentender.uat.bootstrap.ensure_uat_roles`](../../kentender/kentender/uat/bootstrap.py) on migrate:
   - **Strategy Administrator** — full CRUD/submit on strategy hierarchy DocTypes (per matrix).
   - **Strategy Reviewer** — read + workflow approve (`R A`) on strategy DocTypes.

2. **DocType JSON `permissions` regenerated** from the workbook using [`apply_permissions_matrix_from_xlsx.py`](apply_permissions_matrix_from_xlsx.py).  
   - **Strategy DocTypes** (xlsx labels → folder): National Framework → `national_framework`, National Pillar → `national_pillar`, National Objective → `national_objective`, Entity Strategic Plan → `entity_strategic_plan`, Program → `strategic_program`, Sub-Program → `strategic_sub_program`, Indicator → `output_indicator`, Target → `performance_target`.  
   - Script search path includes [`kentender_strategy/.../doctype`](../../kentender_strategy/kentender_strategy/kentender_strategy/doctype).  
   - Maps xlsx role labels to Frappe `Role.name` values (e.g. HoD → **Head of Department**, Opening Chair → **Opening Committee Chair**).  
   - **Bid / Submission** row **Opening Committee** → **Opening Committee Member** for baseline DocPerm (opening-session roles remain assignment-gated in code).  
   - **Award Recommendation** and **Award Decision** rows are **merged** into DocType **Award Decision** (single Frappe DocType).  
   - Every updated DocType keeps a **System Manager** row with full access for administration (not listed per row in the xlsx).

3. **Hooks unchanged** (still required by matrix AS/CL):  
   - **Bid Submission** — `kentender_procurement.services.bid_permission_hooks.bid_submission_has_permission`  
   - **Goods Receipt Note** — validate approved acceptance ([`goods_receipt_note.py`](../../kentender_stores/kentender_stores/kentender_stores/doctype/goods_receipt_note/goods_receipt_note.py))  
   - **Evaluator Assignment** — SoD checks ([`evaluator_assignment.py`](../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/evaluator_assignment/evaluator_assignment.py))

4. **Requisition — Finance Officer** — `controlled_action_service` requires **write** on document for **approve**. The workbook may list **R** only for Finance on Requisition; shipped JSON grants **write** so finance approval steps in workflow and Minimal Golden seed (`approve_requisition_finance`) succeed. If you regenerate DocPerms from the xlsx, re-apply this adjustment or extend the xlsx with **W**/**A** for that cell.

5. **Not applied from xlsx**  
   - **Procurement Template / Version** — no matching shipped DocType in this repo (script skips; add DocType or map to an existing template DocType when available).  
   - **Strategic Revision Record** — not listed in the matrix; DocPerms left as shipped (typically System Manager–only until the matrix defines it).  
   - **Sealed bid / conditional logic (CL)** — not expressible as DocPerm alone; remains **custom logic** (see **Enforcement Rules** sheet and `protected_file_access_service`).

**Permission code mapping (Legend sheet → JSON flags):**  
R → read; W → write (+ read); C → create (+ read); S → submit (+ read); A → write + read (workflow approve); X → cancel; RP → report + read; AS / CL → read baseline (enforcement elsewhere).

**After pulling these changes:** run `bench migrate` on each site so **Custom DocPerm** / cached permissions refresh.

**Related markdown:** [`KenTender Roles and Permissions Matrix.md`](KenTender%20Roles%20and%20Permissions%20Matrix.md) — should stay consistent with the xlsx; if they diverge, **prefer the workbook** as the operational matrix unless product says otherwise.

---

## Automated verification (Role Catalogue ↔ code ↔ golden seed)

**Bench command** (uses `openpyxl` to read the workbook; exits **1** if `MATRIX_ROLE` and the xlsx **Role Catalogue** disagree after label mapping):

```bash
bench --site <site> execute kentender.uat.verify_matrix_alignment.verify_matrix_alignment_console
```

Implementation: [`kentender.uat.verify_matrix_alignment`](../../kentender/kentender/uat/verify_matrix_alignment.py).

**What it checks**

1. **Excel Role Catalogue** (sheet `Role Catalogue`, column *Role Name*) vs **`MATRIX_ROLE`** unique Frappe names, with the same normalizations as elsewhere: *Head of Department (HoD)* → **Head of Department**, *Supplier (External)* → **Supplier**, *System Administrator* → **System Manager**.
2. **Minimal golden** [`minimal_golden_canonical.json`](../../kentender/kentender/uat/minimal_golden/data/minimal_golden_canonical.json): must include **one test user per Role Catalogue row** — internal **System User** accounts for every matrix role except **Supplier**, which uses **two** portal (**Website User**) bidders sharing the **Supplier** role. A dedicated user with **System Manager** covers the matrix “System Administrator” row for end-to-end testing (alongside the built-in Administrator account).

**Deployment note:** `after_migrate` runs [`ensure_uat_roles`](../../kentender/kentender/uat/bootstrap.py), which creates **Frappe Role** rows for every `MATRIX_ROLE` value except built-in **System Manager** (the Role document exists in Frappe core). Run [`verify_matrix_alignment_console`](../../kentender/kentender/uat/verify_matrix_alignment.py) after changing the workbook or golden JSON.
