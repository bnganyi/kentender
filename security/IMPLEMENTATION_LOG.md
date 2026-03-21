# KenTender Security Implementation Log

This log records step-by-step rollout of the security model in:

- `KenTender Security Design Document.md`
- `KenTender_Security_DocPerm_FieldDictionary_CSV_Bundle/*.csv`

## Step 01 - Roles baseline

Date: 2026-03-21  
Site: `kentender.midas.com`

### Objective

Create missing Role records from `Roles_Catalogue.csv` before applying DocPerm, field permlevel, and workflow authority controls.

### Implementation

Added execution helper:

- `kentender/kentender/kentender/security_sync.py`
  - `sync_roles(dry_run=1|0)` reads `Roles_Catalogue.csv`
  - compares expected roles to live `Role` records
  - creates only missing roles when `dry_run=0`

### Execution evidence

Dry run:

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.sync_roles --kwargs '{"dry_run": 1}'`
- Expected roles: 21
- Existing roles before sync: 69
- Missing roles: 10

Apply run:

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.sync_roles --kwargs '{"dry_run": 0}'`
- Created roles: 10

Created role names:

- `Accounting Officer`
- `Accounts Payable Officer`
- `Contract Manager`
- `Department Planning Officer`
- `Evaluation Committee Member`
- `Inspection & Acceptance Officer`
- `Internal Auditor`
- `Oversight Viewer`
- `Planning Authority`
- `Supplier Bidder User`

### Notes

- This step only creates Role masters; it does not assign roles to users.
- Next step: apply `DocPerm_Matrix.csv` by DocType + permlevel.

## Step 01a - Role name normalization

Date: 2026-03-21  
Site: `kentender.midas.com`

### Objective

Normalize role naming to use `Accounting Officer` only.

### Implementation

- Replaced `Accounting Officer / Approving Authority` with `Accounting Officer` in:
  - security CSV bundle files
  - related requirements and implementation log docs
- Merged live role records:
  - `frappe.rename_doc('Role', 'Accounting Officer / Approving Authority', 'Accounting Officer', merge=True, force=True)`

### Verification

- No remaining file references in `apps/kentender` to `Accounting Officer / Approving Authority`.
- Site role exists: `Accounting Officer`
- Old role no longer exists as a separate role.

## Step 02 - DocPerm baseline

Date: 2026-03-21  
Site: `kentender.midas.com`

### Objective

Apply DocType role permissions (by permlevel) from `DocPerm_Matrix.csv` into live `Custom DocPerm`.

### Implementation

Extended execution helper:

- `kentender/kentender/kentender/security_sync.py`
  - `sync_docperms(dry_run=1|0)` reads `DocPerm_Matrix.csv`
  - validates role and doctype prerequisites
  - upserts `Custom DocPerm` rows by key:
    - `doctype` + `role` + `permlevel` + `if_owner`
  - updates permission flags:
    - `select/read/write/create/delete/submit/cancel/amend/report/export/import/share/print/email`
    - `set_user_permissions/mask/apply_user_permissions` (if field exists in current Frappe version)
  - additive/update-only (no deletion of extra existing rows)
  - writes latest sync output to `security/DOCPERM_SYNC_REPORT.md`

### Execution evidence

Dry run before apply:

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.sync_docperms --kwargs '{"dry_run": 1}'`
- CSV rows read: 602
- Unique permission keys: 375
- Missing roles: 0
- Missing doctypes: 34
- Skipped rows: 227
- To create: 375
- To update: 0

Apply run:

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.sync_docperms --kwargs '{"dry_run": 0}'`
- Created rows: 375
- Updated rows: 0

Post-apply idempotency check:

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.sync_docperms --kwargs '{"dry_run": 1}'`
- To create: 0
- To update: 0
- Unchanged: 375

### Notes

- Missing doctypes in the report are expected to remain pending until those DocTypes are created/imported.
- For those doctypes, corresponding DocPerm rows were intentionally skipped (not force-created).
- Next step: apply field-level `permlevel` alignment from `Field_Dictionary.csv` for existing DocTypes/fields.

## Step 03 - Field permlevel baseline

Date: 2026-03-21  
Site: `kentender.midas.com`

### Objective

Apply field-level `permlevel` controls from `Field_Dictionary.csv` to existing fields in existing DocTypes.

### Implementation

Extended execution helper:

- `kentender/kentender/kentender/security_sync.py`
  - `sync_field_permlevels(dry_run=1|0)` reads `Field_Dictionary.csv`
  - matches existing fields in:
    - `Custom Field` (`dt`, `fieldname`)
    - `DocField` (`parent`, `fieldname`)
  - updates only `permlevel`
  - skips missing DocTypes and missing fields
  - writes latest output to `security/FIELD_PERMLEVEL_SYNC_REPORT.md`

### Execution evidence

Dry run before apply:

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.sync_field_permlevels --kwargs '{"dry_run": 1}'`
- CSV rows read: 525
- Unique keys: 305
- Missing doctypes: 36
- Missing fields: 254
- To change: 13

Apply run:

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.sync_field_permlevels --kwargs '{"dry_run": 0}'`
- Changed permlevels: 13

Post-apply idempotency check:

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.sync_field_permlevels --kwargs '{"dry_run": 1}'`
- To change: 0
- Unchanged: 51

### Changed fields (13)

- `Procurement Plan.budget_reference` (0 -> 2)
- `Procurement Plan.revision_reason` (0 -> 1)
- `Procurement Plan.total_reserved_amount` (0 -> 2)
- `Purchase Requisition.budget_reference` (0 -> 2)
- `Purchase Requisition.justification` (0 -> 1)
- `Purchase Requisition.total_committed_amount` (0 -> 2)
- `Purchase Requisition Item.remaining_app_balance` (0 -> 2)
- `Purchase Requisition Item.technical_specification` (0 -> 1)
- `Purchase Requisition Item.tendered_amount` (0 -> 4)
- `Supplier Master.registration_number` (0 -> 2)
- `Supplier Master.tax_id` (0 -> 2)
- `Tender Lot.estimated_value` (0 -> 2)
- `Tender Submission.security_reference` (0 -> 2)

### Notes

- Most `Field_Dictionary.csv` rows currently reference fieldnames not yet present in the live schema.
- This is expected while several target DocTypes/fields are still pending creation or model alignment.
- Next step: workflow authority alignment from `Workflow_Authority.csv`, then user-permission baseline from `User_Permissions.csv`.

## Step 04 - Workflow authority audit

Date: 2026-03-21  
Site: `kentender.midas.com`

### Objective

Assess current workflow transition role authority against `Workflow_Authority.csv` before making workflow changes.

### Implementation

Extended execution helper:

- `kentender/kentender/kentender/security_sync.py`
  - `audit_workflow_authority(write_report=1)`
  - maps CSV family labels to concrete DocTypes where possible
  - compares required and forbidden roles against `Workflow Transition.allowed`
  - outputs audit report to `security/WORKFLOW_AUTHORITY_AUDIT.md`

### Execution evidence

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.audit_workflow_authority --kwargs '{"write_report": 1}'`
- CSV rows read: 16
- Workflow checks performed: 8
- Fully aligned: 3
- Checks with issues: 5
- Missing family references: 1
- Existing DocTypes without workflows: 12

### Current findings (high level)

- One CSV family label not mapped to existing DocType names:
  - `Payment Certificate / Invoice Control`
- Existing DocTypes without any workflow currently:
  - `Acceptance Certificate`, `Award Decision`, `Award Recommendation`, `Bid Opening Record`, `Contract`, `Contract Variation`, `Evaluation Consensus Record`, `Evaluation Worksheet`, `Inspection Report`, `Requisition Tender Handoff`, `Tender Submission`, `Termination Record`
- Role-authority mismatches in current configured workflows:
  - `Procurement Plan Workflow`
  - `Procurement Plan Item Workflow`
  - `Purchase Requisition Workflow`

### Notes

- This step is intentionally audit-only; no workflow transitions were modified automatically.
- Next step: targeted workflow remediation plan (state-by-state), then controlled apply.

## Step 04b - Targeted workflow remediation

Date: 2026-03-21  
Site: `kentender.midas.com`

### Objective

Apply minimal transition-role additions to close identified workflow authority gaps without rewriting workflows.

### Implementation

Extended execution helper:

- `kentender/kentender/kentender/security_sync.py`
  - `remediate_workflow_authority_phase1(dry_run=1|0)`
  - additive-only transition inserts (no deletion/modification of existing transitions)

Applied transition additions:

1. `Procurement Plan Workflow`:
   - `Draft` --`Consolidate`--> `Department Consolidation` as `Department Planning Officer`
2. `Purchase Requisition Workflow`:
   - `Procurement Review` --`Approve Final`--> `Approved` as `Head of Procurement`
3. `Procurement Plan Item Workflow`:
   - `Under Review` --`Approve`--> `Approved` as `Finance/Budget Officer`

### Execution evidence

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.remediate_workflow_authority_phase1 --kwargs '{"dry_run": 0}'`
- Created transitions in final apply: 1 (2 were already present from prior remediation run)

Post-remediation audit:

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.audit_workflow_authority --kwargs '{"write_report": 1}'`
- Workflow checks performed: 8
- Fully aligned checks: 8
- Checks with issues: 0

### Remaining workflow-related gaps

- `Workflow_Authority.csv` contains one family label not yet mapped to concrete doctypes:
  - `Payment Certificate / Invoice Control`
- Existing DocTypes still lacking workflow definitions (12) remain outside this targeted remediation pass and should be handled during Phase 2/3 workflow rollout.

## Step 05 - User permission baseline audit

Date: 2026-03-21  
Site: `kentender.midas.com`

### Objective

Validate row-level permission policy readiness from `User_Permissions.csv` and prepare controlled assignment artifacts.

### Implementation

Extended execution helper:

- `kentender/kentender/kentender/security_sync.py`
  - `audit_user_permission_baseline(write_report=1)`
  - validates role + allow-doctype references
  - measures role-to-user readiness and `allow` doctype record availability
  - writes:
    - `security/USER_PERMISSION_BASELINE_AUDIT.md`
    - `security/USER_PERMISSION_ASSIGNMENTS_TEMPLATE.csv`

### Execution evidence

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.audit_user_permission_baseline --kwargs '{"write_report": 1}'`
- Policy rows read: 16
- Ready policy rows: 16
- Blocked rows: 0
- Missing roles: 0
- Missing allow doctypes: 0
- Users currently assigned to audited roles: 0 across all listed roles

### Notes

- The current CSV is policy-level (`role`, `allow_doctype`, recommendation fields), not concrete assignment-level (`user`, `for_value`).
- No row-level `User Permission` records were auto-created to avoid incorrect cross-entity scoping.
- Next step: populate `USER_PERMISSION_ASSIGNMENTS_TEMPLATE.csv` with real users and values, then run controlled import/apply.

## Step 05b - User permission assignment importer

Date: 2026-03-21  
Site: `kentender.midas.com`

### Objective

Provide a safe, repeatable way to apply concrete `User Permission` rows once assignment data is curated.

### Implementation

Extended execution helper:

- `kentender/kentender/kentender/security_sync.py`
  - `apply_user_permission_assignments(dry_run=1|0)`
  - reads `security/USER_PERMISSION_ASSIGNMENTS_TEMPLATE.csv`
  - validates prerequisites:
    - user exists
    - role exists (if provided)
    - user has role (if role provided)
    - allow doctype exists
    - applicable_for doctype exists (if provided)
    - `for_value` exists in `allow` doctype
  - creates missing `User Permission` rows only (idempotent)
  - writes report to `security/USER_PERMISSION_ASSIGNMENT_SYNC_REPORT.md`

### Execution evidence

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.apply_user_permission_assignments --kwargs '{"dry_run": 1}'`
- Assignment rows read: 0 (template not populated yet)
- To create: 0
- Skipped: 0

### Notes

- This step is ready for execution once assignment rows are filled.
- Current template location:
  - `security/USER_PERMISSION_ASSIGNMENTS_TEMPLATE.csv`

## Step 05c - Assignment suggestion seed

Date: 2026-03-21  
Site: `kentender.midas.com`

### Objective

Generate a starter assignment CSV from policy rows to speed up manual completion.

### Implementation

Extended execution helper:

- `kentender/kentender/kentender/security_sync.py`
  - `generate_user_permission_assignment_suggestions(write_report=1)`
  - creates:
    - `security/USER_PERMISSION_ASSIGNMENTS_SUGGESTED.csv`
    - `security/USER_PERMISSION_ASSIGNMENT_SUGGESTION_REPORT.md`

### Execution evidence

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.generate_user_permission_assignment_suggestions --kwargs '{"write_report": 1}'`
- Policy rows: 16
- Suggested rows: 16
- Placeholder rows (roles with no users currently assigned): 16
- Ambiguous `for_value` rows requiring manual completion: 13

### Notes

- Suggested CSV intentionally includes blank `user` for all rows because no users are currently assigned to the relevant roles.
- Two rows had concrete singleton defaults auto-filled:
  - `Supplier Bidder User` -> `Supplier Master` = `SUPM-2026-00058`
  - `Contract Manager` / `Inspection & Acceptance Officer` -> `Contract` = `CT-2026-00025`
- Next step: assign users to roles, complete `USER_PERMISSION_ASSIGNMENTS_TEMPLATE.csv`, then run assignment apply sync.

## Step 05d - User/role roster export

Date: 2026-03-21  
Site: `kentender.midas.com`

### Objective

Export current active users and their role sets to support role assignment before row-level User Permission application.

### Implementation

Extended execution helper:

- `kentender/kentender/kentender/security_sync.py`
  - `export_user_role_roster(write_report=1)`
  - outputs:
    - `security/USER_ROLE_ROSTER.csv`
    - `security/USER_ROLE_ROSTER_REPORT.md`

### Execution evidence

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.export_user_role_roster --kwargs '{"write_report": 1}'`
- Active non-admin users exported: 1

### Notes

- Current site has one active non-admin system user (`bnganyi@yahoo.com`).
- Next operational step is to assign the new KenTender security roles to actual users, then regenerate suggestions and run assignment sync.

## Step 05e - Test user provisioning and assignment apply

Date: 2026-03-21  
Site: `kentender.midas.com`

### Objective

Use test-environment latitude to provision persona users, assign security roles, and complete row-level User Permission rollout end-to-end.

### Implementation

Extended execution helper:

- `kentender/kentender/kentender/security_sync.py`
  - `provision_test_security_users(dry_run=1|0)`
  - `generate_user_permission_assignment_suggestions(write_report=1)` (updated to keep `applicable_for` blank in starter rows)

Applied approach:

1. Provision 10 persona users with KenTender security roles.
2. Regenerate assignment suggestions from policy + new role memberships.
3. Populate `USER_PERMISSION_ASSIGNMENTS_TEMPLATE.csv` from suggested rows with test defaults:
   - `Company` -> `Midas`
   - `Department` -> `All Departments`
   - `Tender` -> `TN-2026-00059`
4. Apply assignment sync.

### Execution evidence

Provisioning:

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.provision_test_security_users --kwargs '{"dry_run": 0}'`
- Created users: 10
- Assigned role links: 20
- Default password (test users): `Admin@123`

Assignment apply:

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.apply_user_permission_assignments --kwargs '{"dry_run": 0}'`
- Assignment rows read: 16
- Created `User Permission` rows: 11
- Already existing: 5
- Skipped: 0

Post-apply verification:

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.apply_user_permission_assignments --kwargs '{"dry_run": 1}'`
- To create: 0
- Already existing: 16

### Notes

- This is a test/UAT baseline and should be refined before production (especially user-to-entity mapping defaults).
- For production, replace test defaults with real company/department/tender scopes per user.

## Step 06 - UX workspace shell import

Date: 2026-03-21  
Site: `kentender.midas.com`

### Objective

Import the new UX shell (Workspaces, Workspace Sidebars, Desktop Icons) from `ux/kentender-workspace-configs` without failing on unresolved downstream dependencies.

### Implementation

Added execution helper:

- `kentender/kentender/kentender/workspace_sync.py`
  - `sync_ux_workspace_configs(dry_run=1|0)`
  - upserts records from:
    - `ux/kentender-workspace-configs/workspaces/*.json`
    - `ux/kentender-workspace-configs/sidebars/*.json`
    - `ux/kentender-workspace-configs/desktop_icons/*.json`
  - sanitizes unresolved links before insert/update:
    - missing DocType/Report/Page/Workspace targets
    - missing Quick List / Number Card / Dashboard Chart references
    - missing Desktop Icon role rows
  - writes run report to:
    - `security/UX_WORKSPACE_SYNC_REPORT.md`

### Execution evidence

Apply run:

- Command: `bench --site kentender.midas.com execute kentender.kentender.workspace_sync.sync_ux_workspace_configs --kwargs '{"dry_run": 0}'`
- Created:
  - Workspaces: 8
  - Workspace Sidebars: 8
  - Desktop Icons: 8
- Dropped unresolved references during import: 70

Post-import validation:

- Command: `bench --site kentender.midas.com execute kentender.kentender.workspace_validation.validate --kwargs '{"write_report": 1}'`
- Present:
  - `Workspace`: 8/8
  - `Workspace Sidebar`: 8/8
  - `Desktop Icon`: 8/8
  - `Role`: 18/18
- Remaining gaps:
  - `DocType`: 42/59 present (17 missing)
  - `Quick List`: 0/24 present
  - `Number Card`: 1/16 present
  - `Report`: 0/1 present

### Notes

- UX shell is now installed and usable for module navigation in test.
- Missing cards/queues/report and missing DocTypes should be implemented in subsequent content-hardening steps.

## Step 07 - Workspace content placeholders and validator hardening

Date: 2026-03-21  
Site: `kentender.midas.com`

### Objective

Light up workspace cards/report dependencies safely, and correct workspace sync/validation logic to match Frappe v16 workspace models.

### Implementation

- Updated `kentender/kentender/kentender/workspace_sync.py`:
  - quick lists are now validated only by `document_type` existence (not by a non-existent `Quick List` DocType)
- Updated `kentender/kentender/kentender/workspace_validation.py`:
  - removed `Quick List` as a standalone reference type
  - number cards now validate against `number_card_name` (with `label` fallback)
  - charts now validate against `chart_name` (with `label` fallback)
- Extended `kentender/kentender/kentender/security_sync.py` with:
  - `seed_ux_workspace_placeholders(dry_run=1|0)`
  - auto-discovers referenced Number Cards + Reports from UX workspace JSONs
  - creates missing Number Cards (`Document Type`/`ToDo`, `Count`) and missing report stubs
  - writes report to `security/UX_PLACEHOLDER_SEED_REPORT.md`

### Execution evidence

Dry run:

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.seed_ux_workspace_placeholders --kwargs '{"dry_run": 1}'`
- Referenced Number Cards: 16
- To create Number Cards: 16
- Referenced Reports: 1
- To create Reports: 1

Apply run:

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.seed_ux_workspace_placeholders --kwargs '{"dry_run": 0}'`
- Created Number Cards: 16
- Created Reports: 1

Workspace re-sync:

- Command: `bench --site kentender.midas.com execute kentender.kentender.workspace_sync.sync_ux_workspace_configs --kwargs '{"dry_run": 0}'`
- Updated records: 24
- Dropped unresolved references: 32 (all tied to still-missing DocTypes)

Post-step validation:

- Command: `bench --site kentender.midas.com execute kentender.kentender.workspace_validation.validate --kwargs '{"write_report": 1}'`
- Present:
  - `Workspace`: 8/8
  - `Workspace Sidebar`: 8/8
  - `Desktop Icon`: 8/8
  - `Role`: 18/18
  - `Number Card`: 16/16
  - `Report`: 1/1
- Remaining gaps:
  - `DocType`: 42/59 present (17 missing)

### Notes

- Number Card and Report dependencies for the UX shell are now satisfied.
- Remaining UX drops are exclusively from pending DocType models and should clear as those DocTypes are introduced.

## Step 08 - Missing UX DocTypes creation and full workspace restoration

Date: 2026-03-21  
Site: `kentender.midas.com`

### Objective

Create the remaining 17 UX-referenced DocTypes so workspace links/queues no longer drop, then re-align security and workspace records.

### Implementation

Extended `kentender/kentender/kentender/security_sync.py`:

- Added `create_missing_ux_doctypes(dry_run=1|0)`
- Creates placeholder custom DocTypes for the previously missing UX references:
  - `Approval Matrix Rule`, `Award PO Handoff`, `Award Publication Record`, `Bid Opening Register`, `Bid Receipt Log`, `Budget Control Rule`, `Exception Register Entry`, `Post Qualification Check`, `Supplier Bank Detail`, `Supplier Beneficial Ownership`, `Supplier Performance Baseline`, `Supplier Renewal Review`, `Tender Eligibility Rule`, `Tender Evaluation Scheme`, `Tender Security Rule`, `Tender Submission Attachment`, `Tender Submission Lot Response`
- Placeholder defaults:
  - custom non-submittable DocType
  - `autoname = hash`
  - minimal required `title` field
  - baseline `System Manager` DocType permission to allow immediate admin access

### Execution evidence

Dry run:

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.create_missing_ux_doctypes --kwargs '{"dry_run": 1}'`
- Target DocTypes: 17
- Existing: 0
- To create: 17

Apply run:

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.create_missing_ux_doctypes --kwargs '{"dry_run": 0}'`
- Created: 17
- Failed: 0

Post-create alignment:

- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.sync_docperms --kwargs '{"dry_run": 0}'`
  - Created DocPerm rows: 82
  - Updated rows: 1
  - Remaining missing DocTypes in DocPerm matrix: 19 (outside current UX shell scope)
- Command: `bench --site kentender.midas.com execute kentender.kentender.security_sync.sync_field_permlevels --kwargs '{"dry_run": 0}'`
  - Changed permlevels: 0
  - Missing fields remain expected for placeholder schemas
- Command: `bench --site kentender.midas.com execute kentender.kentender.workspace_sync.sync_ux_workspace_configs --kwargs '{"dry_run": 0}'`
  - Dropped unresolved references: 0
- Command: `bench --site kentender.midas.com execute kentender.kentender.workspace_validation.validate --kwargs '{"write_report": 1}'`
  - `DocType`: 59/59 present
  - Overall missing references: None

### Notes

- UX navigation shell is now fully restored with no dropped references.
- These are intentionally minimal placeholder DocTypes; next phase should flesh out fields/workflows for production semantics.
