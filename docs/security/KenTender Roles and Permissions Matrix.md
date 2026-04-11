# KenTender Roles and Permissions Matrix — Role Catalogue

## 1\. Role Classification Model

We divide roles into three types:

**1.1 Permanent Roles (System Roles)**

- Assigned to users in ERPNext
- Define baseline permissions
- Persist across all transactions

**1.2 Session Roles (Committee / Assignment-Based)**

- Not global
- Assigned per:
    - Tender
    - Evaluation
    - Acceptance
- Must be enforced via:
    - assignment
    - custom permission logic

**1.3 Administrative Roles**

- Configure system behavior
- Maintain templates, workflows, permissions

## 2\. Permanent Roles

**2.0 Strategy & Alignment**

**🔹 Strategy Administrator**

**Scope**

- Owns strategic hierarchy and controlled reference data

**Primary Actions**

- Create, edit, submit, and maintain national/entity strategy records (frameworks, pillars, objectives, plans, programs, indicators, targets) per workflow

**🔹 Strategy Reviewer**

**Scope**

- Reviews proposed strategy records and alignment quality

**Primary Actions**

- Review strategy records; recommend or workflow-approve/reject where applicable

_Note: **Planning Authority**, **Procurement Planner**, **Finance Officer**, and **Auditor** also have matrix-defined access to strategy DocTypes (read and/or approve); see workbook **Permissions Matrix** and generated DocType JSON._

**2.1 Requisition & Planning**

**🔹 Requisitioner**

**Scope**

- Create and manage requisitions

**Primary Actions**

- Create requisition
- Edit draft requisition
- Submit requisition

**Access Model**

- Own records only

**🔹 Department Reviewer**

**Scope**

- Internal departmental review

**Primary Actions**

- Review requisition
- Recommend approval/rejection

**🔹 Head of Department (HoD)**

**Scope**

- Department-level approval authority

**Primary Actions**

- Approve/reject requisitions
- Approve template overrides
- Approve planning outputs

**🔹 Procurement Planner**

**Scope**

- Planning and consolidation

**Primary Actions**

- Create plans
- Create plan items
- Allocate requisitions
- Trigger template resolution

**🔹 Planning Authority**

**Scope**

- Final approval of procurement plans

**Primary Actions**

- Approve plans
- Activate plans

**2.2 Finance Roles**

**🔹 Finance Officer**

**Scope**

- Financial validation

**Primary Actions**

- Review financial fields
- Validate funding alignment

**🔹 Budget Controller**

**Scope**

- Budget enforcement

**Primary Actions**

- Confirm budget availability
- Record commitments

**🔹 Accounting Officer**

**Scope**

- Final financial authority

**Primary Actions**

- Approve awards
- Approve high-value contracts

**2.3 Procurement Roles**

**🔹 Procurement Officer**

**Scope**

- End-to-end procurement execution

**Primary Actions**

- Create tenders
- Manage tender lifecycle
- Initiate evaluation
- Prepare award documentation

**🔹 Tender Committee Secretary**

**Scope**

- Administrative coordination

**Primary Actions**

- Manage records
- Coordinate sessions
- Maintain minutes

**🔹 Tender Committee Chair**

**Scope**

- Governance authority in committee processes

**Primary Actions**

- Approve opening
- Approve evaluation reports
- Lead decision-making

**2.4 Supplier Roles**

**🔹 Supplier (External)**

**Scope**

- External interaction via portal

**Primary Actions**

- Submit bids
- Update supplier profile

**🔹 Supplier Compliance Reviewer**

**Scope**

- Supplier verification

**Primary Actions**

- Review documents
- Approve/reject compliance

**2.5 Contract & Execution Roles**

**🔹 Contract Manager**

**Scope**

- Post-award contract lifecycle

**Primary Actions**

- Create contract
- Manage execution
- Track milestones

**🔹 Authorized Signatory**

**Scope**

- Legal authorization

**Primary Actions**

- Sign contracts

**2.6 Inspection & Acceptance Roles**

**🔹 Inspector**

**Scope**

- Perform inspections

**Primary Actions**

- Record inspection results
- Submit inspection reports

**2.7 Stores & Assets Roles**

**🔹 Storekeeper**

**Scope**

- Goods receipt

**Primary Actions**

- Create GRN
- Record goods received

**🔹 Stores Supervisor**

**Scope**

- Oversight of stores operations

**Primary Actions**

- Review GRNs
- Approve store transactions (if required)

**🔹 Asset Officer**

**Scope**

- Asset lifecycle management

**Primary Actions**

- Create assets
- Maintain asset records

**🔹 Asset Custodian**

**Scope**

- Asset holder/user

**Primary Actions**

- Acknowledge asset assignment
- View assigned assets

**2.8 Oversight Roles**

**🔹 Auditor**

**Scope**

- Independent oversight

**Primary Actions**

- View all records
- Review audit trails

**🔹 Complaint Reviewer**

**Scope**

- Complaint handling

**Primary Actions**

- Review complaints
- Recommend resolution

## 3\. Session Roles

These are NOT global permissions.

They MUST be enforced via:

- assignment tables
- custom permission logic

**3.1 Tender Stage**

**🔸 Tender Committee Member (NEW — added)**

**Assigned per Tender**

**Actions**

- Participate in committee deliberations
- View tender data (non-sensitive as per stage)

**🔸 Opening Committee Chair**

**Assigned per Opening Session**

**Actions**

- Control opening process

**🔸 Opening Committee Member**

**Assigned per Opening Session**

**Actions**

- Witness opening

**🔸 Opening Committee Secretary**

**Assigned per Opening Session**

**Actions**

- Record proceedings

**3.2 Evaluation Stage**

**🔸 Evaluator**

**Assigned per Evaluation Session / Lot**

**Actions**

- Score bids

**🔸 Evaluation Committee Chair**

**Assigned per Evaluation Session**

**Actions**

- Approve evaluation report

**🔸 Evaluation Committee Secretary**

**Assigned per Evaluation Session**

**Actions**

- Maintain records

**🔸 Technical Expert**

**Assigned per requirement**

**Actions**

- Provide professional input

**3.3 Acceptance Stage**

**🔸 Acceptance Committee Chair**

**Assigned per Acceptance**

**Actions**

- Approve final acceptance

**🔸 Acceptance Committee Member**

**Assigned per Acceptance**

**Actions**

- Participate in acceptance decisions

**4\. Administrative Roles**

**🔹 System Administrator**

- full system control

**🔹 Template Administrator**

- manage templates and versions

**🔹 Workflow Administrator**

- manage workflows

**🔹 Permission Administrator**

- manage roles and permissions

**🔹 Master Data Administrator**

- manage controlled data

## 5\. Role Behavior Model

**5.1 Permanent Roles**

- defined in Role Permission Manager
- control baseline access

**5.2 Session Roles**

- enforced via:
    - assignment
    - custom has_permission

**5.3 Hybrid Behavior**

Example:

👉 Evaluator = permanent role + assignment

Without assignment:

- NO access

## 6\. Key Design Rules

**Rule 1 — No global access for session roles**

Evaluators, committee members must NEVER have unrestricted access.

**Rule 2 — Assignment overrides role**

Even if user has role, access depends on assignment.

**Rule 3 — Separation of duties enforced**

- Evaluator ≠ Supplier
- Inspector ≠ Storekeeper
- Procurement ≠ Auditor

**Rule 4 — Sensitive stages locked**

- sealed bids
- evaluation confidentiality

## 7\. Final Outcome

This catalogue is now:

✔ complete  
✔ normalized  
✔ aligned to real-world procurement  
✔ implementable in ERPNext

# KenTender Permissions Matrix

## 1\. Permission Model

**1.1 Permission Codes**

| **Code** | **Meaning** |
| --- | --- |
| R   | Read |
| W   | Write/Edit |
| C   | Create |
| S   | Submit |
| A   | Approve (workflow) |
| X   | Cancel |
| RP  | Report Access |
| AS  | Assignment Required |
| CL  | Conditional Logic Required |

**1.2 Key Enforcement Layers**

|     |     |
| --- | --- |
| **Layer** | **Purpose** |
| Role Permission Manager | Base access |
| User Permissions | Row-level filtering |
| Assignment | Session-based restriction |
| Custom Logic | Sealed bids, workflow locks |

## 2\. Core Rule

**Permissions alone are NOT sufficient**  
Critical enforcement = **Assignment + Custom Logic**

## 3\. Requisition & Planning

**3.1 Requisition**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Requisitioner | R C W S | Own records only |
| Department Reviewer | R A | Department scope |
| HoD | R A | Final approval |
| Procurement Planner | R   | Read for planning |
| Auditor | R RP | Read-only |

**3.2 Procurement Plan**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Procurement Planner | R C W S | Full control |
| Planning Authority | R A | Approve + activate |
| HoD | R   | Visibility only |
| Finance Officer | R   | Financial visibility |
| Auditor | R RP | Read-only |

**3.3 Procurement Plan Item**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Procurement Planner | R C W | Full edit |
| HoD | R A | Template override approval |
| Planning Authority | R   | Read |
| Auditor | R RP | Read |

## 4\. Template Governance

**4.1 Procurement Template / Version**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Template Administrator | R C W S | Full control |
| Procurement Planner | R   | Read-only |
| Auditor | R RP | Read |

## 5\. Tendering

**5.1 Tender**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Procurement Officer | R C W S | Full lifecycle |
| Tender Committee Secretary | R W | Admin support |
| Tender Committee Chair | R A | Governance approval |
| Tender Committee Member | R   | Participation |
| HoD | R   | Oversight |
| Auditor | R RP | Read |

## 6\. Submissions & Opening

**6.1 Bid / Submission**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Supplier | R C W S | Own bids only |
| Procurement Officer | R   | Metadata only |
| Opening Committee | R   | After opening only |
| Evaluator | R AS CL | Assigned + post-opening |
| Auditor | R RP | Read |

**🔴 Critical Logic**

- Before opening:
    - NO access to bid content
- After opening:
    - controlled visibility

**6.2 Opening Session**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Opening Chair | R C W S A | Full control |
| Opening Member | R   | View |
| Opening Secretary | R C W S | Admin |
| Procurement Officer | R   | Oversight |
| Auditor | R RP | Read |

## 7\. Evaluation

**7.1 Evaluation Session**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Evaluator | R AS | Assigned only |
| Evaluation Chair | R A | Approve |
| Evaluation Secretary | R W | Admin |
| Procurement Officer | R   | Read |
| Auditor | R RP | Read |

**7.2 Evaluation Score**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Evaluator | R C W AS | Assigned only |
| Evaluation Chair | R   | Review |
| Auditor | R RP | Read |

**7.3 Evaluation Report**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Evaluation Secretary | R C W S | Prepare |
| Evaluation Chair | R A | Approve |
| Accounting Officer | R A | Final approval |
| Procurement Officer | R   | Read |
| Auditor | R RP | Read |

## 8\. Award

**8.1 Award Recommendation**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Procurement Officer | R C W | Prepare |
| Evaluation Chair | R A | Approve |
| Auditor | R RP | Read |

**8.2 Award Decision**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Accounting Officer | R A | Final decision |
| Procurement Officer | R   | Read |
| Auditor | R RP | Read |

## 9\. Contract

**9.1 Contract**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Contract Manager | R C W S | Manage |
| Authorized Signatory | R A | Sign |
| Accounting Officer | R A | Final approval |
| Procurement Officer | R   | Read |
| Auditor | R RP | Read |

## 10\. Acceptance & Inspection

**10.1 Inspection Record**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Inspector | R C W S | Execute |
| Technical Expert | R C W AS | Assigned |
| Auditor | R RP | Read |

**10.2 Acceptance Record**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Acceptance Committee Chair | R A | Final approval |
| Acceptance Committee Member | R AS | Assigned |
| Inspector | R C W | Input |
| Contract Manager | R   | Read |
| Auditor | R RP | Read |

## 11\. Stores

**11.1 GRN (Goods Receipt Note)**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Storekeeper | R C W S | Full |
| Stores Supervisor | R A | Approve (if required) |
| Inspector | R   | Read |
| Auditor | R RP | Read |

**🔴 Critical Logic**

- GRN creation requires:
    - approved acceptance

## 12\. Assets

**12.1 Asset**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Asset Officer | R C W | Full |
| Asset Custodian | R   | Own assets |
| Auditor | R RP | Read |

## 13\. Complaints & Oversight

**13.1 Complaint**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Supplier | R C | Submit |
| Complaint Reviewer | R W | Review |
| Auditor | R RP | Read |

## 14\. System & Audit

**14.1 Approval Action**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| System | C   | Auto-generated |
| Auditor | R RP | Read |

**14.2 Budget Ledger Entry**

|     |     |     |
| --- | --- | --- |
| **Role** | **Permissions** | **Notes** |
| Budget Controller | R C | Manage |
| Finance Officer | R   | View |
| Auditor | R RP | Read |

## 15\. Critical Enforcement Rules

**15.1 Assignment Enforcement**

Applies to:

- Evaluators
- Committee members
- Technical experts

**15.2 Sealed Bid Enforcement**

Before opening:

- NO read access to:
    - documents
    - pricing

**15.3 Workflow Enforcement**

- No direct edits to status
- Only workflow transitions allowed

**15.4 Template Enforcement**

- Templates locked after plan activation

**15.5 GRN Gating**

- Cannot create GRN before acceptance approval

## 16\. Separation of Duties (SoD)

|     |     |
| --- | --- |
| **Conflict** | **Not Allowed** |
| Supplier ↔ Evaluator | ❌   |
| Evaluator ↔ Contract Manager | ❌   |
| Inspector ↔ Storekeeper | ❌   |
| Procurement ↔ Auditor | ❌   |

## 17\. Final Validation Checklist

System is correct when:

- evaluators cannot see unassigned bids
- suppliers cannot access internal data
- GRN blocked before acceptance
- templates not editable post-activation
- workflow cannot be bypassed