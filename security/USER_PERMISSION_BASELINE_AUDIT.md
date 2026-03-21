# KenTender User Permission Baseline Audit (kentender.midas.com)

Source: `/home/midasuser/frappe-bench/apps/kentender/security/KenTender_Security_DocPerm_FieldDictionary_CSV_Bundle/User_Permissions.csv`

## Summary
- CSV policy rows: 16
- Ready policy rows (role+allow doctype exist): 16
- Blocked policy rows (missing role/doctype): 0
- Missing roles: 0
- Missing allow doctypes: 0
- Missing 'recommended_applicable_for' doctypes: 26

## Role assignment readiness (users per role)
- `Accounts Payable Officer`: 0 users
- `Contract Manager`: 0 users
- `Department Planning Officer`: 0 users
- `Evaluation Committee Chair`: 0 users
- `Evaluation Committee Member`: 0 users
- `Finance/Budget Officer`: 0 users
- `Head of Department`: 0 users
- `Inspection & Acceptance Officer`: 0 users
- `Internal Auditor`: 0 users
- `Opening Committee Member`: 0 users
- `Oversight Viewer`: 0 users
- `Procurement Officer`: 0 users
- `Procurement Planner`: 0 users
- `Requestor`: 0 users
- `Supplier Bidder User`: 0 users
- `Supplier Registration Officer`: 0 users

## Allow doctypes and available record counts
- `Company`: 2 records
- `Contract`: 1 records
- `Department`: 27 records
- `Supplier Master`: 1 records
- `Tender`: 4 records

## Missing roles
- None

## Missing allow doctypes
- None

## Missing recommended_applicable_for doctypes
- `All transactional doctypes`
- `Award`
- `Bid Opening Register`
- `Consensus`
- `Contract execution and closeout doctypes`
- `Evaluation Score Record`
- `Handoff`
- `Invoice Control`
- `Payment Certificate`
- `Payment doctypes`
- `Planning`
- `Published`
- `Receipt`
- `Requisition`
- `Retention Register`
- `Revisions`
- `Supplier governance doctypes`
- `Supplier portal doctypes only`
- `Tender Submission*`
- `acceptance doctypes`
- `audit views`
- `award`
- `contract summary`
- `due diligence`
- `inspection`
- `recommendation`

## Next action
- Generate explicit assignments (user, allow, for_value) per active role; this CSV is policy-level and cannot be auto-applied without concrete values.
