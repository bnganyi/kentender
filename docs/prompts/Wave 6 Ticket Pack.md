# Wave 6 Ticket Pack

**Sprint tracker:** [`docs/dev/WAVE 6 BACKLOG.md`](../dev/WAVE%206%20BACKLOG.md) (status / notes only; full tickets remain in this pack).

**Scope**

- **Stores Management**
- **Asset Management**
- **Audit & Oversight Hardening**
- **Transparency & Reporting Layer**

**Wave 6 Epic Overview**

**EPIC-OPS-001 — Stores Management**

Owns:

- goods receipt
- warehouse/store control
- stock movement
- issuance
- reconciliation with procurement + contract + inspection

**EPIC-OPS-002 — Asset Management**

Owns:

- asset creation from procurement
- asset lifecycle
- assignment
- condition tracking
- disposal

**EPIC-GOV-003 — Audit & Oversight**

Owns:

- audit trails (deep)
- cross-module traceability
- audit queries
- compliance flags

**EPIC-GOV-004 — Transparency & Reporting**

Owns:

- public disclosure
- structured reporting
- dashboards (lightweight)
- audit/export datasets

**Recommended Build Order**

**Stores**

1.  OPS-STORY-001 — Store
2.  OPS-STORY-002 — Store Item
3.  OPS-STORY-003 — Goods Receipt Note (GRN)
4.  OPS-STORY-004 — GRN Line
5.  OPS-STORY-005 — Store Ledger Entry
6.  OPS-STORY-006 — Stock Movement
7.  OPS-STORY-007 — Store Issue
8.  OPS-STORY-008 — Store Reconciliation Record
9.  OPS-STORY-009 — receive goods from contract service
10. OPS-STORY-010 — stock issue/transfer services
11. OPS-STORY-011 — store ledger integration and balance computation
12. OPS-STORY-012 — store queue/report scaffolding

**Assets**

1.  OPS-STORY-013 — Asset
2.  OPS-STORY-014 — Asset Category
3.  OPS-STORY-015 — Asset Assignment
4.  OPS-STORY-016 — Asset Condition Log
5.  OPS-STORY-017 — Asset Maintenance Record
6.  OPS-STORY-018 — Asset Disposal Record
7.  OPS-STORY-019 — create asset from GRN/contract service
8.  OPS-STORY-020 — asset lifecycle services
9.  OPS-STORY-021 — asset reporting and tracking scaffolding

**Audit & Oversight**

1.  GOV-STORY-026 — Audit Query
2.  GOV-STORY-027 — Audit Finding
3.  GOV-STORY-028 — Audit Response
4.  GOV-STORY-029 — Audit Action Tracking
5.  GOV-STORY-030 — cross-module trace service
6.  GOV-STORY-031 — audit query/response services
7.  GOV-STORY-032 — audit reporting scaffolding

**Transparency & Reporting**

1.  GOV-STORY-033 — Public Disclosure Record
2.  GOV-STORY-034 — Disclosure Dataset
3.  GOV-STORY-035 — Report Definition
4.  GOV-STORY-036 — Report Execution Log
5.  GOV-STORY-037 — disclosure generation services
6.  GOV-STORY-038 — reporting/export services
7.  GOV-STORY-039 — transparency dashboards (lightweight)

**EPIC-OPS-001 — Stores Management**

**OPS-STORY-001 — Implement Store**

Writing

Implement Store in kentender_operations.

Required fields:

- store_code
- store_name
- store_type
- location
- responsible_department
- store_manager_user
- status
- remarks

Requirements:

- support central store, project store, department store
- add tests

**OPS-STORY-003 — Implement Goods Receipt Note (GRN)**

This is the **bridge between contract → physical delivery → stores**.

Writing

Implement Goods Receipt Note (GRN) in kentender_operations.

Required fields:

- business_id
- contract
- supplier
- store
- receipt_datetime
- received_by_user
- inspection_reference
- acceptance_reference
- status
- total_received_value
- currency
- remarks

Requirements:

- require linkage to contract and inspection/acceptance where applicable
- add tests

Constraints:

- do not update stock directly here (use ledger service)

**OPS-STORY-005 — Implement Store Ledger Entry**

This is the **stock equivalent of Budget Ledger Entry**.

Writing

Implement Store Ledger Entry in kentender_operations.

Required fields:

- store
- item_reference
- entry_type
- entry_direction
- quantity
- unit_of_measure
- posting_datetime
- source_doctype
- source_docname
- remarks

Requirements:

- append-only model
- support receipt, issue, transfer, adjustment
- add tests

Constraints:

- do not store derived balances here

**OPS-STORY-009 — Implement receive-goods-from-contract service**

Writing

Implement receive_goods_from_contract(contract_id, acceptance_record_id).

Requirements:

- create GRN
- create Store Ledger Entries (inbound)
- validate acceptance status
- update contract progress if needed
- add tests

Constraints:

- do not bypass inspection/acceptance layer

**EPIC-OPS-002 — Asset Management**

**OPS-STORY-013 — Implement Asset**

Writing

Implement Asset in kentender_operations.

Required fields:

- asset_code
- asset_name
- asset_category
- source_contract
- source_grn
- supplier
- acquisition_date
- acquisition_cost
- currency
- current_location
- assigned_to_user
- condition_status
- status
- remarks

Requirements:

- link asset to procurement origin
- add tests

**OPS-STORY-019 — Implement create-asset-from-GRN service**

Writing

Implement create_asset_from_grn(grn_id).

Requirements:

- create asset records for qualifying items
- inherit supplier, contract, and cost
- support one-to-many (bulk assets)
- add tests

Constraints:

- do not assume all goods are assets

**EPIC-GOV-003 — Audit & Oversight**

**GOV-STORY-026 — Implement Audit Query**

Writing

Implement Audit Query in kentender_governance.

Required fields:

- business_id
- query_title
- related_doctype
- related_docname
- query_text
- raised_by_user
- raised_on
- status
- response_due_date
- remarks

Requirements:

- allow auditors to raise structured queries
- add tests

**GOV-STORY-030 — Implement cross-module trace service**

This is powerful.

Writing

Implement cross-module trace service in kentender_governance.

Suggested action:

- trace_procurement_chain(object_type, object_id)

Expected output:

- requisition
- plan item
- tender
- bid
- evaluation
- award
- contract
- inspection
- GRN
- asset (if any)

Requirements:

- traverse known linkage fields
- return structured trace graph
- add tests

Constraints:

- keep it readable and explainable

**EPIC-GOV-004 — Transparency & Reporting**

**GOV-STORY-033 — Implement Public Disclosure Record**

Writing

Implement Public Disclosure Record in kentender_governance.

Required fields:

- related_doctype
- related_docname
- disclosure_stage
- disclosure_datetime
- public_summary
- redacted_flag
- published_by_user
- status

Requirements:

- support staged disclosure (tender, award, contract)
- add tests

**GOV-STORY-037 — Implement disclosure generation service**

Writing

Implement disclosure generation service.

Suggested action:

- generate_public_disclosure(object_type, object_id)

Requirements:

- extract non-sensitive fields
- respect disclosure rules
- create Public Disclosure Record
- add tests

Constraints:

- do not expose sensitive data

**Critical Design Insight (Don’t miss this)**

Wave 6 introduces a pattern:

**You now have THREE ledgers**

1.  **Budget Ledger Entry** → money control
2.  **Store Ledger Entry** → stock control
3.  **Contract/Inspection events** → delivery control

Together, they form:

Money → Goods → Assets → Outcomes

If these are consistent, your system becomes audit-grade.

**What this unlocks**

After Wave 6, you can answer:

- Was money spent correctly? (budget ledger)
- Were goods actually received? (GRN + store ledger)
- Were they acceptable? (inspection)
- Where are they now? (store/asset)
- Who is using them? (assignment)
- What did we achieve? (strategy link)

That is full accountability.