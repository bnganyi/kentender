# Roles and Permissions Guidance

**1\. Core principle**

For KenTender, permissions should be based on:

- **business role**
- **entity scope**
- **assignment**
- **workflow stage**
- **sensitivity**

Not just generic read/write.

So a role may:

- read a DocType
- not create it
- create but not approve
- approve but only when assigned
- access only filtered records
- access a report but only if the report query itself respects role scope

That last part is likely why your HOD cannot open **Pending Requisition Approvals**.

**2\. Minimal golden scenario roles**

Use these as the baseline roles:

- Department User / Requisitioner
- Head of Department
- Finance Approver
- Procurement Officer
- Opening Chair
- Evaluator
- Evaluation Chair
- Accounting Officer
- Contract Manager
- Inspection Officer
- Storekeeper
- Asset Officer
- Supplier User
- System Administrator
- Auditor / Oversight

**3\. Minimal DocType permission matrix**

Legend:

- **R** = Read
- **C** = Create
- **W** = Write/Edit
- **S** = Submit / workflow action
- **A** = Approve / stage decision
- **X** = No access
- **F** = Filtered/assigned only
- **RO** = Read-only

**A. Strategy and budget reference objects**

| **DocType** | **Requisitioner** | **HOD** | **Finance** | **Procurement** | **Evaluator** | **Accounting** | **Inspector** | **Storekeeper** | **Asset Officer** | **Supplier** | **Auditor** | **Admin** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| National Framework | RO  | RO  | RO  | RO  | X   | X   | X   | X   | X   | X   | RO  | R/W |
| National Pillar | RO  | RO  | RO  | RO  | X   | X   | X   | X   | X   | X   | RO  | R/W |
| National Objective | RO  | RO  | RO  | RO  | X   | X   | X   | X   | X   | X   | RO  | R/W |
| Entity Strategic Plan | RO  | RO  | RO  | RO  | X   | X   | X   | X   | X   | X   | RO  | R/W |
| Program | RO  | RO  | RO  | RO  | X   | X   | X   | X   | X   | X   | RO  | R/W |
| Sub Program | RO  | RO  | RO  | RO  | X   | X   | X   | X   | X   | X   | RO  | R/W |
| Output Indicator | RO  | RO  | RO  | RO  | X   | X   | X   | X   | X   | X   | RO  | R/W |
| Performance Target | RO  | RO  | RO  | RO  | X   | X   | X   | X   | X   | X   | RO  | R/W |
| Budget Control Period | X   | X   | RO  | RO  | X   | RO  | X   | X   | X   | X   | RO  | R/W |
| Budget | X   | X   | RO  | RO  | X   | RO  | X   | X   | X   | X   | RO  | R/W |
| Budget Line | RO  | RO  | RO  | RO  | X   | RO  | X   | X   | X   | X   | RO  | R/W |
| Budget Ledger Entry | X   | X   | RO  | RO  | X   | RO  | X   | X   | X   | X   | RO  | R/W |

**Notes**

- Requisitioners/HODs should read only the strategy/budget structures needed to create and approve requisitions.
- Budget Ledger should usually be hidden from ordinary users.

**B. Requisition and planning**

| **DocType** | **Requisitioner** | **HOD** | **Finance** | **Procurement** | **Auditor** | **Admin** |
| --- | --- | --- | --- | --- | --- | --- |
| Purchase Requisition | C/R/W/S (own or dept scope) | R/A/F | R/A/F | RO/F | RO  | R/W |
| Purchase Requisition Item | C/R/W (with requisition) | RO  | RO  | RO  | RO  | R/W |
| Requisition Approval Record | RO (own) | R/C/F | R/C/F | R/F | RO  | R/W |
| Requisition Amendment Record | C/R/W (if allowed by workflow) | R/A/F | R/A/F | R/A/F | RO  | R/W |
| Procurement Plan | X   | RO/F | RO/F | C/R/W/S/A | RO  | R/W |
| Procurement Plan Item | X   | RO/F | RO/F | C/R/W/S/A | RO  | R/W |
| Requisition Planning Link | RO/F | RO/F | RO/F | C/R/W | RO  | R/W |
| Plan Consolidation Source | X   | X   | X   | C/R/W | RO  | R/W |
| Procurement Plan Approval Record | X   | X   | RO/F | R/C/A | RO  | R/W |
| Plan Fragmentation Alert | X   | X   | RO/F | R/W/F | RO  | R/W |

**Notes**

- HOD should see departmental requisitions awaiting their action.
- Finance should see requisitions routed for budget/finance validation.
- Procurement owns planning.

**C. Tender and bids**

| **DocType** | **Procurement** | **Opening Chair** | **Evaluator** | **Evaluation Chair** | **Supplier** | **Auditor** | **Admin** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Tender | C/R/W/S/A | RO/F | RO/F | RO/F | RO/F (published only) | RO  | R/W |
| Tender Lot | C/R/W | RO  | RO  | RO  | RO/F | RO  | R/W |
| Tender Criteria | C/R/W | RO  | RO/F | RO/F | RO/F | RO  | R/W |
| Tender Document | C/R/W | RO/F | RO/F | RO/F | RO/F (published only) | RO  | R/W |
| Tender Approval Record | R/C/A | RO  | X   | X   | X   | RO  | R/W |
| Tender Visibility Rule | C/R/W | X   | X   | X   | X   | RO  | R/W |
| Tender Clarification | R/W | X   | X   | X   | C/R/W (own side if portal supports) | RO  | R/W |
| Tender Amendment | C/R/W/A | RO/F | RO/F | RO/F | RO/F | RO  | R/W |
| Bid Submission | RO/F | RO/F | X before opening; RO/F after opening as assigned | RO/F | C/R/W/S (own only before deadline) | RO  | R/W |
| Bid Document | RO/F controlled | RO/F controlled | controlled/assigned | controlled/assigned | C/R/W (own only) | RO controlled | R/W |
| Bid Receipt | RO/F | RO/F | X   | X   | RO (own only) | RO  | R/W |
| Bid Withdrawal Record | RO/F | RO/F | X   | X   | C/R (own only before deadline) | RO  | R/W |
| Bid Opening Session | RO/F | C/R/W/S/A/F | X   | X   | X   | RO  | R/W |
| Bid Opening Attendance | RO/F | C/R/W/F | X   | X   | RO/F if published summary allowed | RO  | R/W |
| Bid Opening Register | RO/F | R/F | RO/F after opening | RO/F after opening | RO/F if disclosure allowed | RO  | R/W |
| Bid Opening Event Log | RO/F | R/C/F | X   | X   | X   | RO  | R/W |

**Notes**

- Supplier must never see internal evaluation or opening internals beyond lawful disclosure.
- Evaluators should not see sealed bid content pre-opening.
- Opening Chair needs explicit access to opening session and register.

**D. Evaluation and award**

| **DocType** | **Evaluator** | **Evaluation Chair** | **Procurement** | **Accounting** | **Auditor** | **Admin** |
| --- | --- | --- | --- | --- | --- | --- |
| Evaluation Session | R/F | R/W/S/A/F | RO/F | RO/F | RO  | R/W |
| Evaluation Stage | R/F | R/W/F | RO/F | RO/F | RO  | R/W |
| Evaluator Assignment | RO (own) | R/W/F | RO/F | X   | RO  | R/W |
| Conflict Declaration | C/R/W (own) | R/F | X   | X   | RO  | R/W |
| Evaluation Record | C/R/W/S (assigned only) | RO/F + finalize controls | RO/F | X   | RO  | R/W |
| Evaluation Score Line | C/R/W (assigned only) | RO/F | X   | X   | RO  | R/W |
| Evaluation Disqualification Record | propose only if assigned | A/R/W/F | RO/F | X   | RO  | R/W |
| Evaluation Aggregation Result | X direct edit | RO/F | RO/F | RO/F | RO  | R/W |
| Evaluation Report | RO/F | C/R/W/S/A/F | RO/F | RO/F | RO  | R/W |
| Evaluation Approval / Submission Record | RO/F | C/R/F | RO/F | X   | RO  | R/W |
| Award Decision | X   | RO/F | C/R/W/A/F | A/F | RO  | R/W |
| Award Approval Record | X   | X   | C/R/F | C/R/A/F | RO  | R/W |
| Award Deviation Record | X   | X   | C/R/W/F | A/F | RO  | R/W |
| Award Notification | X   | X   | R/W/F | R/W/F | X   | RO  |
| Standstill Period | X   | X   | R/W/F | R/W/A/F | RO  | R/W |
| Award Outcome Line | X   | RO/F | R/W/F | RO/F | X   | RO  |
| Award Return Record | X   | X   | C/R/W/F | C/R/W/F | RO  | R/W |

**Notes**

- Evaluator must not approve award.
- Accounting Officer should not edit scoring.
- Procurement can prepare award, but final approval belongs elsewhere.

**E. Contract, inspection, stores, assets**

| **DocType** | **Procurement** | **Contract Manager** | **Inspector** | **Storekeeper** | **Asset Officer** | **Auditor** | **Admin** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Contract | C/R/W/S/A/F | R/W/F | RO/F | RO/F | RO/F | RO  | R/W |
| Contract Party | R/W/F | R/W/F | RO/F | X   | X   | RO  | R/W |
| Contract Milestone | R/W/F | R/W/F | RO/F | X   | X   | RO  | R/W |
| Contract Deliverable | R/W/F | R/W/F | RO/F | X   | X   | RO  | R/W |
| Contract Variation | C/R/W/F | C/R/W/F | X   | X   | X   | RO  | R/W |
| Contract Approval Record | R/C/A/F | RO/F | X   | X   | X   | RO  | R/W |
| Contract Signing Record | R/W/F | R/W/F | X   | X   | X   | RO  | R/W |
| Contract Status Event | RO/F | RO/F | RO/F | X   | X   | RO  | R/W |
| Inspection Method Template | RO  | RO  | RO  | X   | X   | RO  | R/W |
| Inspection Record | RO/F | RO/F | C/R/W/S/A/F | X   | X   | RO  | R/W |
| Inspection Checklist Line | RO/F | RO/F | C/R/W/F | X   | X   | RO  | R/W |
| Inspection Parameter Line | RO/F | RO/F | C/R/W/F | X   | X   | RO  | R/W |
| Inspection Test Result | X   | X   | C/R/W/F | X   | X   | RO  | R/W |
| Sample Record | X   | X   | C/R/W/F | X   | X   | RO  | R/W |
| Inspection Evidence | RO/F | RO/F | C/R/W/F | X   | X   | RO controlled | R/W |
| Non Conformance Record | RO/F | R/F | C/R/W/F | X   | X   | RO  | R/W |
| Acceptance Record | RO/F | RO/F | C/R/W/S/A/F | X   | X   | RO  | R/W |
| Reinspection Record | X   | RO/F | C/R/W/F | X   | X   | RO  | R/W |
| Goods Receipt Note | RO/F | RO/F | RO/F | C/R/W/S/F | X   | RO  | R/W |
| GRN Line | X   | X   | X   | C/R/W/F | X   | RO  | R/W |
| Store Ledger Entry | X   | X   | X   | RO/F | X   | RO  | R/W |
| Stock Movement | X   | X   | X   | C/R/W/S/F | X   | RO  | R/W |
| Store Issue | X   | X   | X   | C/R/W/S/F | X   | RO  | R/W |
| Store Reconciliation Record | X   | X   | X   | C/R/W/S/F | X   | RO  | R/W |
| Asset | RO/F | RO/F | RO/F | RO/F | C/R/W/S/F | RO  | R/W |
| Asset Assignment | X   | X   | X   | X   | C/R/W/S/F | RO  | R/W |
| Asset Condition Log | X   | X   | X   | X   | C/R/W/F | RO  | R/W |
| Asset Maintenance Record | X   | X   | X   | X   | C/R/W/F | RO  | R/W |
| Asset Disposal Record | X   | X   | X   | X   | C/R/W/S/A/F | RO  | R/W |

**4\. Report and query permission matrix**

This is probably the part currently broken for you.

**Procurement reports**

| **Report** | **Requisitioner** | **HOD** | **Finance** | **Procurement** | **Auditor** | **Admin** |
| --- | --- | --- | --- | --- | --- | --- |
| My Requisitions | Yes | Optional | Optional | Optional | Yes | Yes |
| Pending Requisition Approvals | No  | **Yes** | **Yes** | Optional | Yes | Yes |
| Planning Ready Requisitions | No  | No  | Optional | Yes | Yes | Yes |
| Planning Queue | No  | No  | Optional | Yes | Yes | Yes |
| Draft Procurement Plans | No  | No  | Optional | Yes | Yes | Yes |
| Active Procurement Plans | No  | Optional RO | Optional RO | Yes | Yes | Yes |
| Draft Tenders | No  | No  | No  | Yes | Yes | Yes |
| Published Tenders | Public/internal filtered | RO  | RO  | Yes | Yes | Yes |
| Scheduled Opening Sessions | No  | No  | No  | Yes | Yes | Yes |
| Opening Registers | No  | No  | No  | Opening roles + Procurement + Auditor | Yes | Yes |

**Evaluation and award reports**

| **Report** | **Evaluator** | **Eval Chair** | **Procurement** | **Accounting** | **Auditor** | **Admin** |
| --- | --- | --- | --- | --- | --- | --- |
| My Assigned Evaluations | **Yes** | Yes | No  | No  | Yes | Yes |
| Conflict Declarations Pending | Own only | Yes | No  | No  | Yes | Yes |
| Evaluation Sessions In Progress | Assigned only | Yes | Yes | Optional RO | Yes | Yes |
| Ranked Bid Summary | No direct if sensitive | Yes | Yes | Yes | Yes | Yes |
| Awards Pending Approval | No  | No  | Yes | Yes | Yes | Yes |
| Awards Pending Final Approval | No  | No  | Optional | **Yes** | Yes | Yes |
| Standstill Active Awards | No  | No  | Yes | Yes | Yes | Yes |

**Contract / inspection / stores / assets reports**

| **Report** | **Contract Manager** | **Inspector** | **Storekeeper** | **Asset Officer** | **Auditor** | **Admin** |
| --- | --- | --- | --- | --- | --- | --- |
| Active Contracts | Yes | RO  | RO  | RO  | Yes | Yes |
| Contracts Pending Signature | Yes | No  | No  | No  | Yes | Yes |
| Scheduled Inspections | Optional RO | **Yes** | No  | No  | Yes | Yes |
| Inspections Awaiting Acceptance | RO  | **Yes** | No  | No  | Yes | Yes |
| Goods Pending Receipt | RO  | RO  | **Yes** | No  | Yes | Yes |
| Procurement Goods Receipts | RO  | No  | **Yes** | Optional RO | Yes | Yes |
| Pending Asset Registration | No  | No  | Optional RO | **Yes** | Yes | Yes |
| Procured Assets | RO  | RO  | RO  | **Yes** | Yes | Yes |

**5\. Specific fix for your screenshot issue**

For **Pending Requisition Approvals**, best practice is:

**Allowed roles**

- Head of Department
- Finance Approver
- Procurement Officer only if the report includes procurement-approval stage items
- Auditor / Oversight
- System Administrator

**Not needed**

- Department User
- Supplier
- Evaluator
- Storekeeper
- Asset Officer

**Important**

Even if the role can access the report, the query must still filter correctly.

For example:

**HOD should only see**

- requisitions where:
    - hod_user = current user
    - or requesting_department belongs to their department scope
    - and workflow_state = Pending HOD Approval

**Finance should only see**

- requisitions routed to finance stage

**Procurement should only see**

- requisitions routed to procurement stage

So the fix is usually **two-part**:

1.  give the role access to the report
2.  fix report filters so users only see valid rows

**6\. Best-practice permission rules for reports**

For every report:

**A. Report-level access**

Who can open the report at all

**B. Row-level filtering**

Which records they can see

**C. Column-level sensitivity**

Hide sensitive columns where needed

For example, a role may open Pending Requisition Approvals but still only see:

- business ID
- title
- department
- amount
- due date

and not:

- internal exception notes
- sensitive justification text
- audit-only metadata

**7\. Recommended implementation model**

Use this pattern for each report in KenTender:

**Report access**

Grant to the role families that truly need it

**Query filter**

Apply one of:

- current user ownership
- department scope
- entity scope
- assignment scope
- workflow-state scope

**Example for HOD**

workflow_state = "Pending HOD Approval"  
AND hod_user = current_user

**Example for finance**

workflow_state = "Pending Finance Approval"  
AND procuring_entity IN allowed_finance_entities

**8\. Recommended minimal golden permissions baseline**

If you want the shortest usable baseline, enforce these:

**HOD**

Can open:

- My Work
- Pending Requisition Approvals
- Department Requisitions

**Finance**

Can open:

- Pending Requisition Approvals
- Budget-related requisition queues

**Procurement**

Can open:

- Planning Queue
- Draft Tenders
- Published Tenders
- Contract queues

**Evaluator**

Can open:

- My Assigned Evaluations only

**Accounting**

Can open:

- Awards Pending Final Approval

**Inspector**

Can open:

- Scheduled Inspections
- Inspections Awaiting Acceptance

**Storekeeper**

Can open:

- Goods Pending Receipt
- Procurement Goods Receipts

**Asset Officer**

Can open:

- Pending Asset Registration
- Procured Assets

**9\. Strong recommendation**

Do **not** try to solve this only with DocType permissions.

For KenTender, correct access requires:

- DocType permission
- workflow-state service checks
- assignment checks
- report access
- report row filters

That is the real model.

**10\. Practical next step**

The best next artifact is a **full KenTender Role Access Permissions Workbook** with sheets for:

- role catalogue
- DocType matrix
- report matrix
- workflow action matrix
- sensitivity rules
- row-filter rules

That will be much easier for your developers and testers to implement and verify consistently.