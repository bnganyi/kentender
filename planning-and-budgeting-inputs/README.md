# KenTender Phase 1 Implementation Package

This package is a build-starting baseline for the **public-sector Procurement Planning & Budgeting** module.
It is intentionally focused on Kenyan public procurement controls and APP governance.

## Contents
- `implementation_guide.docx` — human-readable implementation blueprint
- `doctypes/` — starter Frappe DocType JSON definitions
- `workflows/` — starter workflow JSON definitions
- `python/kentender_phase1/` — hooks, validation scaffolding, utility functions, and scheduler placeholders
- `config/role_permission_matrix.csv` — role/permission starter matrix
- `config/report_catalog.csv` — reporting backlog for Phase 1

## Important notes
1. These files are **starter artifacts**, not a drop-in production module.
2. Budget availability checks must be wired to the target ERPNext Budget / GL model in the deployment environment.
3. Threshold values and approval sequences must be loaded from the procuring entity's approved policy data.
4. APP publishing should generate a real PDF attachment and immutable snapshot in the final build.
5. Anti-split logic is intentionally conservative and should be refined with entity-approved heuristics during UAT.

## Suggested implementation order
1. Reference masters and policy tables
2. Procurement Plan and Procurement Plan Item
3. Workflow and permissions
4. Budget control / commitment wiring
5. Revision / publication / lock
6. Requisition handoff
7. Reporting and dashboards
