# KenTender CLM Implementation Pack

This pack converts the CLM design into starter build artifacts for a Frappe/ERPNext app.

## Included
- `fixtures/custom_fields.json` — custom fields for ERPNext core DocTypes and CLM support DocTypes
- `fixtures/workflows.json` — workflow definitions for CLM
- `kentender/hooks.py` — starter hooks
- `kentender/services/*.py` — starter integration and workflow guard modules
- `kentender/workflows/*.json` — per-workflow readable definitions

## Notes
- These are starter artifacts, not a drop-in finished app.
- Role names must exist in your site before activating workflows.
- Some workflow guards assume matching custom fields and DocType names exist.
- ERPNext core DocTypes leveraged: Project, Task, Quality Inspection, Purchase Receipt, Purchase Invoice, Payment Entry, Company, Supplier, Employee, Department.

## Build sequence
1. Create the custom DocTypes in your app:
   - Contract
   - Contract Implementation Team Member
   - Inspection Committee Member
   - Acceptance Certificate
   - Retention Ledger
   - Retention Release Request
   - Contract Variation
   - Claim
   - Dispute Case
   - Termination Record
   - Defect Liability Case
   - Monthly Contract Monitoring Report
   - Contract Activity Log
2. Import/apply `custom_fields.json`
3. Import/apply `workflows.json`
4. Copy Python modules into your app and wire `hooks.py`
5. Run migrations
6. Test in this order:
   - Contract signing/activation
   - Milestone lifecycle
   - Certificate gating of invoice
   - Retention deduction/release
   - Variation / claims / disputes / termination
   - Close-out / DLP
   - Monthly monitoring report generation

## Recommended roles
- Head of Procurement
- Accounting Officer
- Contract Implementation Team
- Inspection and Acceptance Committee
- Head of User Department
- Head of Finance
- Supplier


## Added in this update
- `kentender/doctypes/*.json` — starter custom DocType JSON files for all CLM custom entities

## Important
- These DocType JSON files are design-aligned starter definitions.
- Depending on your Frappe version and app packaging approach, you may still need to convert them into full app DocType folders/metadata or recreate/import them through developer mode.
- Field ordering, naming series, permissions, and list/form behavior still need final hardening in your actual app.


## Permission pack
Added:
- `fixtures/permission_matrix.json` — authoritative role/doctypes permission mapping
- `fixtures/permission_matrix.csv` — spreadsheet-friendly version
- `fixtures/roles.json` — starter role fixture
- `fixtures/role_permissions_reference.json` — reference structure for configuring DocPerms

### Important permission notes
- These are starter permissions, not final production security.
- User Permissions by Company should still be configured to enforce company-level data isolation.
- Portal/Supplier access must be further restricted with permission query conditions and server-side guards.
- Native ERPNext DocTypes such as Purchase Invoice, Project, Task, Quality Inspection, and Purchase Receipt may already have permissions in your site; merge carefully instead of blindly overwriting.
