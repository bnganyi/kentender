# KenTender eProcurement System Architecture

KenTender v1.0

Contents

[Introduction 4](#_Toc224670220)

[A. System Requirements 5](#_Toc224670221)

[WAVE 1: PROCUREMENT PLANNING & REQUISITIONS 5](#_Toc224670222)

[1\. Procurement Planning & Budgeting 5](#_Toc224670223)

[2\. Purchase Requisitions 5](#_Toc224670224)

[WAVE 2: SUPPLIER REGISTRATION + TENDERING 5](#_Toc224670225)

[1\. Supplier Registration – Best Practice Model 5](#_Toc224670226)

[2\. Tender Document Preparation 5](#_Toc224670227)

[3\. Tender Submission & Opening – Expanded Controls 5](#_Toc224670228)

[4\. Evaluation & Award – Advanced Best Practice Controls 5](#_Toc224670229)

[WAVE 3: CONTRACT MANAGEMENT 5](#_Toc224670230)

[1\. Contract Execution & Administration 5](#_Toc224670231)

[2\. Contract Execution (Operational Management) 6](#_Toc224670232)

[3\. Inspection & Acceptance 8](#_Toc224670233)

[4\. Financial Management (Payments & Retentions) 9](#_Toc224670234)

[5\. Claims, Disputes & Performance Adjustments 10](#_Toc224670235)

[6\. Contract Variations & Amendments 11](#_Toc224670236)

[7\. Contract Termination 12](#_Toc224670237)

[8\. Contract Closeout & Defects Liability 12](#_Toc224670238)

[9\. Monitoring & Reporting 13](#_Toc224670239)

[B. Data Dictionary 15](#_Toc224670240)

[1\. Phase 1 Core Entities: 15](#_Toc224670241)

[C. Workflow Definition 23](#_Toc224670242)

[1\. Workflow Philosophy for the System 23](#_Toc224670243)

[2\. Required System Roles 23](#_Toc224670244)

[3\. Document Workflows 23](#_Toc224670245)

[4\. KenTender Workflow Configuration Fields 27](#_Toc224670246)

[5\. Required System Automations 28](#_Toc224670247)

[6\. Critical Compliance Features 28](#_Toc224670248)

[D. Phase 1 Procurement System Architecture 30](#_Toc224670249)

[1\. Entity Relationship Diagram 30](#_Toc224670250)

[2\. KenTender Implementation Matrix 30](#_Toc224670251)

[3\. UI and Screen Architecture 34](#_Toc224670252)

[4\. Proposed KenTender App Structure 35](#_Toc224670253)

[5\. Procurement Lifecycle State Machine 35](#_Toc224670254)

[E. Role–Permission Matrix 42](#_Toc224670255)

[1\. Roles Definition 42](#_Toc224670256)

[2\. Permission Levels 42](#_Toc224670257)

[3\. Full Permission Matrix 42](#_Toc224670258)

[4\. Special Restrictions 44](#_Toc224670259)

# Introduction

This document defines the architecture of the KenTender system at the following levels:

- System requirements
- Data dictionary
- Workflow definition
- Field standards and naming conventions
- Document numbering conventions
- Entity relationship diagrams
- Roles and permissions

# System Requirements

## WAVE 1: PROCUREMENT PLANNING & REQUISITIONS

The system aims to strengthen:

- Traceability to national strategy
- Budget discipline
- Demand justification controls
- Audit trail integrity

### Procurement Planning & Budgeting

#### Strategic Alignment Layer (Best Practice Addition)

System must require linkage between:

- National Development Plan (e.g., Vision 2030 / CIDP / MTP)
- Ministerial / County Strategic Plans
- Corporate Plan
- Department Work Plan
- Individual Procurement Line Item

**Requirement:**  
Every procurement line must reference:

- Strategic objective code
- Program
- Sub-program
- Output indicator
- Performance target

This enables:

- Performance-based procurement
- Audit traceability
- Anti-fragmentation controls

#### Annual Procurement Plan (APP) Controls

Add:

- Unique APP ID per financial year
- Version control (V1, V2, Supplementary Plan)
- Audit trail of all modifications
- Locking after Accounting Officer approval
- Supplementary plan workflow with justification memo

#### Budget Controls (Critical)

System must:

1.  Integrate with IFMIS (or mock interface layer)
2.  Validate:
    - Budget vote
    - Program code
    - Remaining allocation
3.  Prevent:
    - Over-commitment
    - Duplicate line items
    - Splitting of procurement to avoid thresholds

**Add:**

- Commitment accounting (encumbrance at requisition stage)
- Real-time budget consumption dashboard
- Multi-year project budgeting capability

#### Threshold & Method Advisory Engine

System should:

- Automatically recommend procurement method based on:
    - Estimated value
    - Type (goods, works, services)
    - Emergency flag
    - Framework agreement usage
- Enforce legal thresholds (PPADA)

This reduces method manipulation.

### Purchase Requisitions

More internal controls are needed here.

#### Requisition Justification Controls

Each requisition must include:

- Need justification statement
- Confirmation that item is not available in stores
- Technical specs upload
- Cost estimate with basis (market survey, historical price, engineer estimate)
- Risk classification (low/medium/high value)

#### Conflict of Interest Declaration (Mandatory)

Before approval:

- Requesting officer declares no conflict of interest.
- Digital signature required.

#### Workflow Enhancements

Add:

- Parallel review capability (technical + finance simultaneously)
- SLA tracking per approval stage
- Escalation rules if approvals are delayed
- Delegation matrix

#### Audit & Integrity Layer

System logs:

- IP address
- Timestamp
- Edits
- Deleted requisitions (soft delete only)

This is crucial for public procurement compliance.

## WAVE 2: SUPPLIER REGISTRATION + TENDERING

### Supplier Registration – Best Practice Model

#### Supplier Risk Scoring Engine

System automatically assigns risk score based on:

- New supplier vs established
- Single-director companies
- Related directors across multiple vendors
- History of debarment
- Litigation history
- Repeated award patterns

This aligns with international (e.g., OECD) anti-corruption controls.

#### Ownership Transparency

Add:

- Beneficial ownership declaration (mandatory)
- PEP (Politically Exposed Person) screening
- Cross-check directors against public office holders

System flags conflicts if:

- Director matches procuring entity employee
- Same auditor across competing bidders (risk indicator)

#### Debarment & Blacklist Module

System should integrate with:

- PPRA debarment list
- World Bank debarment list
- EACC flagged entities

Auto-block participation if debarred.

#### Document Expiry Engine

For:

- Tax Compliance Certificate
- Business Permit
- Professional registration
- Auditor certificate
- Insurance certificates

System must:

- Send reminders before expiry
- Suspend supplier automatically after expiry
- Block bid submission if expired

#### Market Structure Analytics

Expand:

- Market concentration report per category
- Number of active suppliers per category
- Red flag if < 3 suppliers repeatedly bid

### Tender Document Preparation

This must enforce standardization.

#### Standard Bidding Document (SBD) Library

System must include:

- Open Tender SBD
- Restricted Tender SBD
- RFQ template
- RFP template
- Framework Agreement template
- Two-stage tender template

Editable but locked core clauses.

#### Automated Clause Control

System auto-inserts:

- Tender security percentage
- Performance security percentage
- Evaluation criteria
- Preference/reservation (AGPO, youth/women/PLWD)
- Local content requirements

Based on procurement method + threshold.

#### Pre-Bid Clarification Module

Add:

- Online Q&A window
- Anonymous clarification publication
- Addendum issuance workflow
- Auto-extension of deadline if addendum issued late

This is the best international practice.

#### Tender Timeline Controls

System should enforce:

- Minimum advertisement days per method
- Standstill period
- Automatic closure at deadline (no admin override)

### Tender Submission & Opening – Expanded Controls

This is where e-procurement must be airtight.

#### Secure Bid Encryption

System should:

- Encrypt bids upon submission
- Prevent access until official opening time
- Log digital opening committee attendance

#### Electronic Tender Opening Ceremony

System generates:

- Bid opening minutes automatically
- List of bidders
- Bid prices
- Tender security details
- Digital signatures of opening committee

#### Late Submission Prevention

System must:

- Hard lock at deadline
- No admin override
- Record server time (not user time)

### Evaluation & Award – Advanced Best Practice Controls

#### Evaluation Committee Controls

System must:

- Register evaluation committee members
- Require conflict of interest declaration
- Prevent evaluator access before opening
- Prevent score changes after submission (unless logged)

#### Scoring Engine (For RFP)

Weighted criteria:

- Technical score auto-calculated
- Financial score formula locked
- Combined score auto-ranked

No manual rank editing.

#### Due Diligence Checklist Engine

System generates checklist for:

- Site visit
- Financial capacity validation
- Reference checks
- Equipment verification

Must be completed before award recommendation.

#### Professional Opinion Template

Structured template:

- Compliance summary
- Evaluation summary
- Risk commentary
- Recommendation
- Legal compliance check

#### Standstill & Appeal Automation

System must:

- Enforce 14-day standstill
- Block contract signing during appeal
- Log PPARB case reference number
- Track outcome

## WAVE 3: CONTRACT MANAGEMENT

### Contract Execution & Administration

#### Purpose

This module governs the transition from **award to active contract**, ensuring that contractual obligations are formally established, legally binding, and operationally actionable.

It creates the foundation for:

- Execution
- Monitoring
- Payment
- Compliance enforcement

#### Operational Requirements

The system must support:

- Preparation of a **contract agreement** by the Head of Procurement
- Electronic signing by:
    - Supplier / Contractor (successful tenderer)
    - Accounting Officer
- Distribution of signed contract to:
    - User Department
    - Contract Implementation Team (CIT)
- Appointment of:
    - Contract Implementation Team (CIT)
    - Inspection & Acceptance Committee (IAC)
- Communication and coordination across:
    - Procurement
    - User Department
    - Finance
    - Supplier

#### System Capabilities

**Contract Creation**

- Generate contract automatically from:
    - Approved Award Decision
- Maintain linkage to:
    - Tender
    - Supplier
    - Procurement Plan Item

**Contract Document Management**

- Upload and manage:
    - Contract Agreement
- Support:
    - Version control
    - Document history

**Electronic Signature Workflow**

- Enable digital signing sequence:
    1.  Supplier signs
    2.  Accounting Officer signs
- Capture:
    1.  Timestamp
    2.  User identity
    3.  Signature audit trail

**Contract Distribution**

- Automatically notify and grant access to:
    - User Department
    - CIT

**Team Formation**

- Record:
    - CIT members
    - IAC members
- Capture roles:
    - Chair
    - Member
    - Secretary
    - Non-member

**Control Layer**

- Contract becomes active only after full execution
- Signed contracts are immutable
- All actions logged for audit

### Contract Execution (Operational Management)

#### Purpose

This module manages the **day-to-day execution of the contract**, ensuring that deliverables are performed according to agreed milestones and documented through structured oversight.

#### Operational Requirements

The system must support:

**For Works Contracts**

- Site handover procedures
- Progress meetings (Minutes of Meeting – MoM)
- Milestone tracking

**For Goods Contracts**

- Delivery tracking
- Testing and verification
- Milestone-based delivery confirmation

**General Execution Activities**

- Recording of:
    - CIT meetings
    - Progress updates
    - Issues and risks

#### System Capabilities

**Milestone Management**

- Define milestones at contract setup:
    - Description
    - Timeline
    - Value
    - Acceptance criteria
- Track:
    - Planned vs actual completion

**CIT Activity Management**

- Record:
    - Site handover reports
    - Meeting minutes (MoM)
    - Progress updates
- Attach supporting documents

**Collaboration**

- Enable interaction between:
    - CIT
    - Supplier
    - Procurement

**Control Layer**

- Milestones must be predefined before execution
- Execution records must be timestamped and auditable

### Inspection & Acceptance

#### Purpose

To ensure that all deliverables meet contractual and technical requirements through **independent verification and structured certification**.

#### Operational Requirements

The system must support:

- Notification to Inspection & Acceptance Committee (IAC) upon milestone completion
- Execution of:
    - Tests
    - Inspections
- Recording:
    - Results
    - Observations
- Issuance of:
    - Interim certificates
    - Acceptance decisions

#### System Capabilities

**Inspection Trigger**

- Automatically notify IAC when:
    - CIT confirms milestone completion

**Inspection Recording**

- Capture:
    - Test criteria
    - Results
    - Pass/fail decisions

**Certification Management**

Support issuance of:

- Interim Certificate
- Certificate of Conformity (technical – User Department)
- Certificate of Acceptance (non-technical – Procurement)
- Final Acceptance Certificate (FAC)

**Goods Receipt**

- Generate:
    - Goods Received Note (GRN)
- Allow:
    - Committee sign-off

**Control Layer**

- Inspection must precede acceptance
- Certificates must be linked to verified milestones
- All approvals must be role-restricted

### Financial Management (Payments & Retentions)

#### Purpose

To ensure that all financial transactions are **accurate, justified, and aligned with contract performance**, while maintaining compliance with financial regulations.

#### Operational Requirements

The system must support:

- Submission of invoices by supplier
- Validation against:
    - Completed milestones
    - Approved certificates
- Processing of:
    - Interim payments
    - Final payment

#### System Capabilities

**Invoice Management**

- Allow supplier to:
    - Submit invoices per milestone
- Link invoice to:
    - Certificate
    - Milestone

**Payment Processing**

- Route invoice:
    - Head of Procurement → Finance
- Generate:
    - Payment Voucher
- Capture:
    - Bank details
    - Payment approvals

**Retention Management**

- Automatically:
    - Deduct retention %
- Track:
    - Retention balances
- Support:
    - Release after defined period

**Statutory Compliance**

- Integrate with:
    - Tax systems (e.g., ETR)
- Support:
    - Tax deduction validation
    - Reporting

**Control Layer**

- Payment cannot occur without certification
- Retention must be enforced automatically
- Financial actions must be fully auditable

### Claims, Disputes & Performance Adjustments

#### Purpose

To manage contractual risks by providing structured mechanisms for **claims, penalties, incentives, and dispute resolution**.

#### Operational Requirements

The system must support:

- Submission of claims by:
    - Supplier
    - Procuring Entity
- Recording:
    - Liquidated damages
    - Penalties
- Management of:
    - Disputes
    - Mediation processes

#### System Capabilities

**Claims Management**

- Provide templates for:
    - Claims
    - Payment demands
- Track:
    - Claim status
    - Supporting documents

**Penalty Calculation**

- Automatically compute:
    - Liquidated damages
- Generate:
    - Demand notices

**Dispute Tracking**

- Record:
    - Dispute notices
    - Mediation steps
    - Outcomes

**Stop Work Orders**

- Allow Accounting Officer to:
    - Issue stop-work orders
- Record:
    - Justification
    - Supporting documents

**Control Layer**

- Claims must be documented and traceable
- Penalty calculations must follow predefined rules
- Disputes must be auditable

### Contract Variations & Amendments

#### Purpose

To manage controlled changes to contract scope, time, or cost while maintaining transparency and approval discipline.

#### Operational Requirements

The system must support:

- Submission of variation requests
- Evaluation and approval workflows
- Tracking of:
    - Cost impact
    - Time extensions

#### System Capabilities

- Record variation details
- Link to original contract
- Track cumulative changes

**Control Layer**

- Variations must require approval
- All changes must be version-controlled

### Contract Termination

#### Purpose

To manage early contract closure in a controlled and legally compliant manner.

#### Operational Requirements

The system must support:

- Initiation of termination
- Issuance of notices
- Settlement of:
    - Payments
    - Penalties
    - Retentions

#### System Capabilities

- Record:
    - Termination reason
    - Supporting documents
- Manage:
    - Site handover
    - Contractor exit

**Control Layer**

- Termination must require:
    - Legal basis
    - Supporting documentation

### Contract Closeout & Defects Liability

#### Purpose

To formally conclude contracts and manage post-completion obligations.

#### Operational Requirements

The system must support:

- Final acceptance of deliverables
- Handover to user department
- Start of defect liability period

#### System Capabilities

**Closeout**

- Issue Final Acceptance Certificate (FAC)
- Trigger final payment

**Defect Liability Management**

- Track defect liability period
- Allow contract reopening for defects

**Asset / Output Handover**

- Record:
    - Asset transfer
    - Operational responsibility

**Control Layer**

- Contract cannot close without final acceptance
- Defect liability must be tracked

### Monitoring & Reporting

#### Purpose

To provide visibility into contract performance, financial exposure, and compliance.

#### Operational Requirements

The system must support:

- Monthly reporting by Head of Procurement
- Monitoring of:
    - Milestones
    - Payments
    - Retentions

#### System Capabilities

Generate reports:

- Contract Progress Report
- Outstanding Payments Report
- Retention Summary
- Claims & Disputes Log

**Control Layer**

- Reports must reflect real-time system data
- Data must be audit-consistent

# Data Dictionary

### Phase 1 Core Entities:

- National Development Plan
- National Development Priority
- Corporate Strategic Plan
- Strategic Objective
- Procurement Plan
- Procurement Plan Item
- Purchase Requisition
- Requisition Item
- Supplier Profile
- Supplier Compliance Document
- Tender
- Tender Lot
- Tender Document
- Bid Submission
- Bid Document
- Evaluation Committee
- Evaluation Scorecard
- Award Decision
- Procurement Method
- Evaluation Criteria

#### National Development Plan

Represents the **national government development framework** (for example, a 5-year development plan).

DocType Name: National Development Plan

**Purpose**

Stores national strategic priorities so procurement activities can be aligned with them.

|     |     |     |     |
| --- | --- | --- | --- |
| Field | Type | Required | Description |
| plan_name | Data | Yes | Name of the development plan |
| plan_code | Data | Yes | Unique identifier |
| start_year | Int | Yes | Start year |
| end_year | Int | Yes | End year |
| adopting_authority | Data | Yes | Authority approving the plan |
| approval_date | Date | Yes | Approval date |
| status | Select | Yes | Draft / Active / Expired |
| description | Long Text | No  | Overview of the plan |
| document_reference | Attach | No  | Official plan document |
| total_budget_projection | Currency | No  | Estimated national spending |
| created_by | Link (User) | Yes | Creator |
| creation_date | Datetime | Yes | System timestamp |

#### National Development Priority

Child table to store **priorities within the national plan**.

DocType Name: National Development Priority

Parent: **National Development Plan**

|     |     |     |     |
| --- | --- | --- | --- |
| Field | Type | Required | Description |
| priority_code | Data | Yes | Unique code |
| priority_title | Data | Yes | Priority name |
| sector | Select | Yes | Infrastructure / Health / Agriculture / ICT / Education |
| description | Small Text | Yes | Priority description |
| target_outcome | Small Text | No  | Expected outcome |
| kpi | Data | No  | Performance indicator |

#### Corporate Strategic Plan

Represents the **strategic plan of a ministry, department, or agency (MDA)**.

DocType Name: Corporate Strategic Plan

**Purpose**

Aligns an organization’s activities with the **National Development Plan**.

|     |     |     |     |
| --- | --- | --- | --- |
| Field | Type | Required | Description |
| plan_name | Data | Yes | Strategic plan name |
| plan_code | Data | Yes | Unique code |
| entity | Link (Company) | Yes | Ministry / agency |
| national_plan | Link (National Development Plan) | Yes | Parent national plan |
| start_year | Int | Yes | Start year |
| end_year | Int | Yes | End year |
| approval_authority | Data | Yes | Approving authority |
| approval_date | Date | Yes | Approval date |
| status | Select | Yes | Draft / Active / Expired |
| document_reference | Attach | No  | Uploaded plan |
| description | Long Text | No  | Overview |

#### Strategic Objective

Child table under **Corporate Strategic Plan**.

DocType Name: Strategic Objective

|     |     |     |     |
| --- | --- | --- | --- |
| Field | Type | Required | Description |
| objective_code | Data | Yes | Unique identifier |
| objective_title | Data | Yes | Objective title |
| priority | Link (National Development Priority) | Yes | Linked national priority |
| description | Small Text | Yes | Objective description |
| performance_indicator | Data | No  | KPI |
| target_value | Data | No  | Target value |
| responsible_department | Link (Department) | Yes | Owner |

#### Procurement Plan

Represents the **Annual Procurement Plan (APP)**.

DocType Name: **Procurement Plan**

|     |     |     |     |
| --- | --- | --- | --- |
| Field | Type | Required | Description |
| plan_name | Data | Yes | APP identifier |
| entity | Link (Company) | Yes | Procuring entity |
| financial_year | Link (Fiscal Year) | Yes | Fiscal year |
| plan_type | Select | Yes | Annual / Supplementary |
| development_plan_reference | Data | No  | Link to national development plan |
| corporate_plan_reference | Data | No  | Corporate strategic plan |
| budget_reference | Data | Yes | Budget approval reference |
| budget_approval_date | Date | Yes | Approval date |
| budget_approved_by | Link (User) | Yes | Approving authority |
| status | Select | Yes | Draft / Submitted / Approved / Locked |
| total_budget | Currency | Yes | Total APP value |
| created_by_department | Link (Department) | Yes | Responsible department |
| remarks | Small Text | No  | Notes |

#### Procurement Plan Item

DocType Name: Procurement Plan Item

|     |     |     |     |
| --- | --- | --- | --- |
| Field | Type | Required | Description |
| parent_plan | Link (Procurement Plan) | Yes | Parent APP |
| procurement_reference | Data | Yes | Procurement code |
| strategic_plan | Link (Corporate Strategic Plan) | Yes | Strategic plan reference |
| strategic_objective | Link (Strategic Objective) | Yes | Objective served |
| national_priority | Link (National Development Priority) | Yes | National alignment |
| description | Small Text | Yes | Description |
| category | Select | Yes | Goods / Works / Services |
| estimated_cost | Currency | Yes | Estimated value |
| procurement_method | Select | Yes | Open / RFQ / RFP / Direct |
| funding_source | Data | Yes | Budget line |
| quarter | Select | Yes | Q1 / Q2 / Q3 / Q4 |
| responsible_department | Link (Department) | Yes | Owner |
| status | Select | Yes | Planned / Initiated / Completed |

Example traceability for national / strategic / corporate plan linkage:

Tender: Hospital Equipment  
↓  
Procurement Plan Item  
↓  
Strategic Objective: Improve rural health services  
↓  
Corporate Strategic Plan: Ministry of Health Strategic Plan 2024–2029  
↓  
National Development Priority: Universal Healthcare  
↓  
National Development Plan: Vision 2030

Auditors can now verify **public funds align with national priorities**.

#### Purchase Requisition

Initiates a procurement request from a department.

DocType Name: Purchase Requisition

|     |     |     |     |
| --- | --- | --- | --- |
| Field | Type | Required | Description |
| requisition_number | Data | Yes | Unique ID |
| department | Link (Department) | Yes | Requesting dept |
| request_date | Date | Yes | Date submitted |
| requested_by | Link (User) | Yes | Officer |
| procurement_plan_item | Link (Procurement Plan Item) | Yes | APP reference |
| budget_line | Data | Yes | Budget code |
| estimated_cost | Currency | Yes | Estimated value |
| justification | Text | Yes | Procurement justification |
| technical_specification | Long Text | Yes | Specifications |
| status | Select | Yes | Draft / Submitted / Finance Review / Approved / Rejected |
| hod_approval | Check | No  | Head of dept approval |
| finance_validation | Check | No  | Budget validation |
| accounting_officer_approval | Check | No  | Final approval |

#### Requisition Item

Child table under Purchase Requisition.

DocType Name: Requisition Item

|     |     |     |     |
| --- | --- | --- | --- |
| Field | Type | Required | Description |
| item_name | Data | Yes | Item name |
| description | Small Text | Yes | Description |
| quantity | Float | Yes | Quantity |
| unit_of_measure | Link (UOM) | Yes | UOM |
| estimated_unit_price | Currency | Yes | Price estimate |
| estimated_total | Currency | Yes | Auto calculated |

#### Supplier Profile

Master supplier registry.

DocType Name: Supplier Profile

|     |     |     |     |
| --- | --- | --- | --- |
| Field | Type | Required | Description |
| supplier_name | Data | Yes | Legal name |
| supplier_type | Select | Yes | Company / Individual |
| registration_number | Data | Yes | Company registration |
| registration_registry | Select | Yes | BRS / NGO Board / Others |
| registration_date | Date | Yes | Date registered |
| tax_pin | Data | Yes | KRA PIN |
| tax_compliance_certificate | Data | Yes | TCC number |
| tcc_expiry_date | Date | Yes | Expiry |
| address | Text | Yes | Physical address |
| email | Data | Yes | Email |
| phone | Data | Yes | Phone |
| website | Data | No  | Website |
| market_structure | Select | No  | Monopoly / Oligopoly / Competitive |
| status | Select | Yes | Pending / Approved / Suspended |

#### Supplier Compliance Document

Child table.

DocType Name: Supplier Compliance Document

|     |     |     |     |
| --- | --- | --- | --- |
| Field | Type | Required | Description |
| document_type | Select | Yes | TCC / License / Permit |
| document_number | Data | Yes | ID  |
| issue_date | Date | Yes | Issue date |
| expiry_date | Date | Yes | Expiry |
| issuing_authority | Data | Yes | Authority |
| document_file | Attach | Yes | Uploaded document |
| verification_status | Select | Yes | Pending / Verified / Rejected |

#### Tender

Represents the procurement event.

DocType Name: Tender

|     |     |     |     |
| --- | --- | --- | --- |
| Field | Type | Required | Description |
| tender_number | Data | Yes | Tender ID |
| procurement_plan_item | Link | Yes | APP reference |
| procurement_method | Select | Yes | Open / RFQ / RFP |
| tender_title | Data | Yes | Title |
| tender_description | Text | Yes | Description |
| publication_date | Date | Yes | Publication date |
| submission_deadline | Datetime | Yes | Deadline |
| opening_date | Datetime | Yes | Opening ceremony |
| tender_security_required | Check | No  | Security requirement |
| tender_security_amount | Currency | No  | Security amount |
| status | Select | Yes | Draft / Published / Closed / Evaluated / Awarded |

#### Tender Lot

Child table under Tender.

DocType Name: Tender Lot

|     |     |     |
| --- | --- | --- |
| Field | Type | Required |
| lot_number | Data | Yes |
| description | Small Text | Yes |
| estimated_value | Currency | Yes |
| delivery_location | Data | Yes |

#### Tender Document

Tender attachments.

DocType Name: Tender Document

**Fields**

|     |     |
| --- | --- |
| Field | Type |
| document_type | Select |
| document_file | Attach |
| version | Data |
| upload_date | Date |

#### Bid Submission

Represents a supplier bid.

DocType Name: Bid Submission

|     |     |
| --- | --- |
| Field | Type |
| tender | Link (Tender) |
| supplier | Link (Supplier Profile) |
| submission_time | Datetime |
| bid_amount | Currency |
| tender_security_issuer | Data |
| tender_security_number | Data |
| security_expiry | Date |
| status | Select (Submitted / Withdrawn / Amended) |

#### Bid Document

Bid attachments.

DocType Name: Bid Document

|     |     |
| --- | --- |
| Field | Type |
| document_type | Data |
| document_file | File |
| upload_time | Datetime |

#### Evaluation Committee

DocType Name: Evaluation Committee

|     |     |
| --- | --- |
| Field | Type |
| tender | Link |
| member_name | Data |
| member_role | Select |
| institution | Data |
| conflict_of_interest_declared | Check |

#### Evaluation Scorecard

DocType Name: Evaluation Scorecard

|     |     |
| --- | --- |
| Field | Type |
| bid | Link |
| criteria | Data |
| max_score | Float |
| score | Float |
| comments | Small Text |

#### Award Decision

DocType Name: Award Decision

|     |     |
| --- | --- |
| Field | Type |
| tender | Link |
| winning_supplier | Link |
| evaluated_price | Currency |
| award_date | Date |
| decision_reference | Data |
| approved_by | Link (User) |

#### Procurement Method

DocType Name: Procurement Method

|     |     |
| --- | --- |
| Field | Type |
| name | Data |

#### Evaluation Criteria

DocType Name: Evaluation Criteria

|     |     |
| --- | --- |
| Field | Type |
| name | Data |
| score | Number |

### Phase 2 Core Entities:

- Contract
- Contract Milestone
- Contract Team
- Contract Activity Log
- Inspection And Acceptance Record
- Contract Certificate
- Goods Received Note
- Supplier Invoice
- Payment Voucher
- Contract Claim
- Contract Dispute
- Contract Variation
- Contract Termination
- Defect Liability Record

#### Contract

Represents the formal agreement between the procuring entity and the awarded supplier/contractor.

**DocType Name: Contract**

**Purpose**

Serves as the master record for all contract-related activities, linking award decisions to execution, financial management, and closeout.

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Required** | **Description** |
| contract_number | Data | Yes | Unique contract identifier |
| tender | Link (Tender) | Yes | Source tender |
| award_decision | Link (Award Decision) | Yes | Approved award reference |
| supplier | Link (Supplier Profile) | Yes | Contracted supplier |
| contract_title | Data | Yes | Contract title |
| contract_type | Select | Yes | Works / Goods / Services |
| contract_value | Currency | Yes | Total contract value |
| start_date | Date | Yes | Contract start date |
| end_date | Date | Yes | Contract end date |
| retention_percentage | Percent | No  | Retention amount |
| status | Select | Yes | Draft / Active / Suspended / Completed / Terminated |
| signed_contract_document | Attach | No  | Final signed contract |
| created_by | Link (User) | Yes | Creator |
| creation_date | Datetime | Yes | System timestamp |

#### Contract Milestone

Defines deliverables and execution stages tied to the contract.

**DocType Name: Contract Milestone**

**Parent: Contract**

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Required** | **Description** |
| milestone_name | Data | Yes | Milestone title |
| description | Small Text | Yes | Milestone details |
| milestone_type | Select | Yes | Delivery / Stage / Payment |
| planned_date | Date | Yes | Expected completion |
| milestone_value | Currency | Yes | Financial value |
| acceptance_criteria | Small Text | Yes | Conditions for acceptance |
| status | Select | Yes | Pending / In Progress / Completed / Approved |

#### Contract Team

Stores all assigned contract-related personnel.

**DocType Name: Contract Team**

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Required** | **Description** |
| contract | Link (Contract) | Yes | Associated contract |
| member_name | Data | Yes | Name of member |
| role | Select | Yes | CIT / IAC |
| designation | Select | Yes | Chair / Member / Secretary / Non-member |
| institution | Data | No  | Organization |
| contact_details | Data | No  | Contact info |

#### Contract Activity Log

Captures execution activities such as meetings and site handover.

**DocType Name: Contract Activity Log**

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Required** | **Description** |
| contract | Link (Contract) | Yes | Associated contract |
| activity_type | Select | Yes | Meeting / Site Handover / Progress Update |
| activity_date | Date | Yes | Date of activity |
| description | Text | Yes | Details |
| attachment | Attach | No  | Supporting document |

#### Inspection And Acceptance Record

Captures inspection results and acceptance decisions.

**DocType Name: Inspection And Acceptance Record**

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Required** | **Description** |
| contract | Link (Contract) | Yes | Associated contract |
| milestone | Link (Contract Milestone) | Yes | Related milestone |
| inspection_date | Date | Yes | Inspection date |
| test_details | Text | Yes | Tests conducted |
| result | Select | Yes | Passed / Failed / Conditional |
| decision | Select | Yes | Accepted / Accepted with Penalty / Rejected |
| remarks | Small Text | No  | Notes |
| attachment | Attach | No  | Supporting evidence |

#### Contract Certificate

Represents all certification types issued during contract lifecycle.

**DocType Name: Contract Certificate**

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Required** | **Description** |
| contract | Link (Contract) | Yes | Associated contract |
| certificate_type | Select | Yes | Interim / Conformity / Acceptance / Final Acceptance |
| milestone | Link (Contract Milestone) | No  | Related milestone |
| issue_date | Date | Yes | Date issued |
| issued_by | Link (User) | Yes | Issuer |
| remarks | Small Text | No  | Notes |
| certificate_document | Attach | No  | Certificate file |

#### Goods Received Note (GRN)

Records receipt of goods and committee sign-off.

**DocType Name: Goods Received Note**

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Required** | **Description** |
| contract | Link (Contract) | Yes | Associated contract |
| milestone | Link (Contract Milestone) | Yes | Related milestone |
| receipt_date | Date | Yes | Date received |
| received_by | Data | Yes | Receiver |
| status | Select | Yes | Pending / Verified / Approved |
| attachment | Attach | No  | Supporting document |

#### Supplier Invoice

Represents invoices submitted by supplier.

**DocType Name: Supplier Invoice**

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Required** | **Description** |
| contract | Link (Contract) | Yes | Associated contract |
| milestone | Link (Contract Milestone) | Yes | Related milestone |
| invoice_number | Data | Yes | Supplier invoice number |
| invoice_date | Date | Yes | Invoice date |
| invoice_amount | Currency | Yes | Amount claimed |
| status | Select | Yes | Submitted / Verified / Approved / Paid |
| attachment | Attach | No  | Invoice document |

#### Payment Voucher

Represents internal payment processing document.

**DocType Name: Payment Voucher**

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Required** | **Description** |
| contract | Link (Contract) | Yes | Associated contract |
| invoice | Link (Supplier Invoice) | Yes | Linked invoice |
| voucher_number | Data | Yes | Internal reference |
| amount | Currency | Yes | Payment amount |
| payment_date | Date | No  | Date paid |
| status | Select | Yes | Draft / Verified / Approved / Paid |

#### Contract Claim

Captures claims from supplier or procuring entity.

**DocType Name: Contract Claim**

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Required** | **Description** |
| contract | Link (Contract) | Yes | Associated contract |
| claim_type | Select | Yes | Payment / Interest / Damages |
| submitted_by | Select | Yes | Supplier / Procuring Entity |
| claim_date | Date | Yes | Submission date |
| claim_amount | Currency | Yes | Amount |
| description | Text | Yes | Claim details |
| status | Select | Yes | Submitted / Under Review / Approved / Rejected |

#### Contract Dispute

Tracks disputes and resolution processes.

**DocType Name: Contract Dispute**

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Required** | **Description** |
| contract | Link (Contract) | Yes | Associated contract |
| dispute_reference | Data | Yes | Unique ID |
| dispute_date | Date | Yes | Date raised |
| description | Text | Yes | Details |
| resolution_status | Select | Yes | Open / Under Mediation / Resolved |
| outcome | Small Text | No  | Final decision |

#### Contract Variation

Captures approved changes to contract.

**DocType Name: Contract Variation**

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Required** | **Description** |
| contract | Link (Contract) | Yes | Associated contract |
| variation_type | Select | Yes | Scope / Time / Cost |
| description | Text | Yes | Details |
| impact_amount | Currency | No  | Cost change |
| time_extension_days | Int | No  | Time added |
| approval_status | Select | Yes | Draft / Approved / Rejected |

#### Contract Termination

Records contract termination details.

**DocType Name: Contract Termination**

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Required** | **Description** |
| contract | Link (Contract) | Yes | Associated contract |
| termination_date | Date | Yes | Date |
| reason | Text | Yes | Justification |
| notice_issued | Check | Yes | Notice sent |
| settlement_amount | Currency | No  | Final settlement |
| status | Select | Yes | Initiated / Approved / Completed |

#### Defect Liability Record

Tracks defects after completion.

**DocType Name: Defect Liability Record**

|     |     |     |     |
| --- | --- | --- | --- |
| **Field** | **Type** | **Required** | **Description** |
| contract | Link (Contract) | Yes | Associated contract |
| defect_description | Text | Yes | Issue |
| reported_date | Date | Yes | Date |
| resolved_date | Date | No  | Resolution date |
| status | Select | Yes | Open / Resolved |

# Workflow Definition

### Workflow Philosophy for the System

The workflow must enforce five core procurement controls:

1.  **Separation of duties**  
    No officer should approve their own request.
2.  **Budget validation before tender  
    **Finance must validate funds before procurement proceeds.
3.  **Immutable tender deadlines**  
    Once published, tender deadlines cannot be changed without cancellation.
4.  **Controlled evaluation**  
    Evaluation committee members must declare **conflict of interest** before accessing bids.
5.  **Accounting officer final authority**  
    Award decisions require **Accounting Officer approval**.

### Required System Roles

|     |     |
| --- | --- |
| Role | Responsibility |
| Procurement Officer | Creates procurement plans and tenders |
| Department Officer | Creates requisitions |
| Head of Department | Approves requisitions |
| Finance Officer | Validates budget |
| Procurement Manager | Oversees tender process |
| Evaluation Committee Member | Scores bids |
| Evaluation Committee Chair | Submits final evaluation |
| Accounting Officer | Final approval of awards |
| Supplier | Submits bids |
| Auditor | Read-only access |

### Document Workflows

**Workflow 1: Procurement Plan**

DocType: **Procurement Plan**

**States**

Draft  
Submitted  
Under Review  
Approved  
Locked

**Workflow Table**

|     |     |     |     |
| --- | --- | --- | --- |
| Current State | Action | Next State | Allowed Role |
| Draft | Submit | Submitted | Procurement Officer |
| Submitted | Review | Under Review | Procurement Manager |
| Under Review | Approve | Approved | Accounting Officer |
| Approved | Lock | Locked | System |

**Rules**

- Once **Locked**, APP cannot be edited.
- Only **Supplementary Plans** may modify it.

**Workflow 2: Purchase Requisition**

DocType: **Purchase Requisition**

**States**

Draft  
Submitted  
Department Approval  
Finance Review  
Procurement Review  
Approved  
Rejected

**Workflow Table**

|     |     |     |     |
| --- | --- | --- | --- |
| Current | Action | Next | Role |
| Draft | Submit | Submitted | Department Officer |
| Submitted | Approve | Department Approval | Head of Department |
| Department Approval | Validate Budget | Finance Review | Finance Officer |
| Finance Review | Forward | Procurement Review | Finance Officer |
| Procurement Review | Approve | Approved | Procurement Manager |
| Any State | Reject | Rejected | Approver |

**Rules**

- Requester **cannot approve their own requisition**.
- Budget must exist before approval.

**Workflow 3: Tender Lifecycle**

DocType: **Tender**

**States**

Draft  
Internal Approval  
Published  
Closed  
Opening Complete  
Evaluation  
Award Pending  
Awarded  
Cancelled

**Workflow Table**

|     |     |     |     |
| --- | --- | --- | --- |
| Current | Action | Next | Role |
| Draft | Submit | Internal Approval | Procurement Officer |
| Internal Approval | Approve | Published | Procurement Manager |
| Published | Auto Close | Closed | System |
| Closed | Open Bids | Opening Complete | Procurement Manager |
| Opening Complete | Start Evaluation | Evaluation | Procurement Manager |
| Evaluation | Submit Report | Award Pending | Evaluation Chair |
| Award Pending | Approve Award | Awarded | Accounting Officer |
| Any | Cancel | Cancelled | Accounting Officer |

**Critical System Controls**

Once **Published**:

- Documents cannot be edited
- Deadline cannot change
- Supplier list becomes locked

**Workflow 4: Bid Submission**

DocType: **Bid Submission**

**States**

Submitted  
Withdrawn  
Locked  
Opened  
Evaluated

**Workflow Table**

|     |     |     |     |
| --- | --- | --- | --- |
| Current | Action | Next | Role |
| Submitted | Withdraw | Withdrawn | Supplier |
| Submitted | Lock | Locked | System |
| Locked | Open | Opened | Procurement Manager |
| Opened | Evaluate | Evaluated | Evaluation Committee |

**Rules**

- Submissions **automatically lock at deadline**
- Opening creates **electronic opening record**

**Workflow 5: Evaluation**

DocType: **Evaluation Scorecard**

**States**

Draft  
Submitted  
Reviewed  
Finalized

**Workflow**

|     |     |     |     |
| --- | --- | --- | --- |
| Current | Action | Next | Role |
| Draft | Submit Score | Submitted | Committee Member |
| Submitted | Review | Reviewed | Committee Chair |
| Reviewed | Finalize | Finalized | Committee Chair |

**Controls**

Committee members must:

- declare **Conflict of Interest**
- sign **evaluation declaration**

before scoring.

**Workflow 6: Award Decision**

DocType: **Award Decision**

**States**

Draft  
Submitted  
Approved  
Rejected  
Published

**Workflow**

|     |     |     |     |
| --- | --- | --- | --- |
| Current | Action | Next | Role |
| Draft | Submit | Submitted | Procurement Manager |
| Submitted | Approve | Approved | Accounting Officer |
| Submitted | Reject | Rejected | Accounting Officer |
| Approved | Publish | Published | System |

**Controls**

Award must generate:

- **Notification to all bidders**
- **Standstill period**
- **Public notice**

**Workflow 7: National Development Plan**

Draft  
Approved  
Active  
Archived

**Workflow 8: Corporate Strategic Plan**

Draft  
Submitted  
Approved  
Active  
Expired

### KenTender Workflow Configuration Fields

Define:

- Workflow Name
- Document Type
- Workflow State Field

Example:

Workflow Name: Tender Workflow  
Document Type: Tender  
State Field: workflow_state

Then define:

- States
- Transitions
- Allowed Roles
- Actions

### Required System Automations

These should be implemented as **server scripts or hooks**.

1.  **Deadline Lock**

At submission deadline lock all Bid Submission records

1.  **Tender Auto Close**

Scheduler job:

if now >= submission_deadline  
set tender status = Closed

1.  **Supplier Compliance Check**

Before bid acceptance:

verify supplier compliance documents

1.  **Evaluation Access Control**

Committee members can only see:

assigned tender bids

1.  **Automatic Notifications**

Trigger notifications for:

- Tender published
- Bid submitted
- Bid opened
- Award decision

### Critical Compliance Features

These are extremely important for audit:

1.  **Immutable Logs**

Every action recorded:

- timestamp
- user
- action
- record affected

1.  **Document Hashing**

Bid documents should store **SHA256 hash** to prove they were **not altered**.

1.  **Conflict of Interest Register**

Committee members must fill **COI declaration** before evaluation.

# Phase 1 Procurement System Architecture

### Entity Relationship Diagram

### KenTender Implementation Matrix

Build DocTypes in this order:

**Step 1 — Strategic Layer**

1.  National Development Plan
2.  National Development Priority
3.  Corporate Strategic Plan
4.  Strategic Objective

|     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- |
| DocType | Type | Parent | Workflow | Permissions | Custom Logic |
| National Development Plan | Master | —   | Yes | Admin / Planning Authority | Prevent edit once active |
| National Development Priority | Child | National Development Plan | No  | Planning Authority | None |
| Corporate Strategic Plan | Master | —   | Yes | Planning Authority | Validate date overlap |
| Strategic Objective | Child | Corporate Strategic Plan | No  | Planning Authority | Link to national priority |

Notes:

- These entities change **rarely**.
- Mostly used for **alignment and reporting**.

**Step 2 — Procurement Planning**

1.  Procurement Plan
2.  Procurement Plan Item

|     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- |
| DocType | Type | Parent | Workflow | Permissions | Custom Logic |
| Procurement Plan | Transaction | —   | Yes | Procurement Officer / Accounting Officer | Generate APP number |
| Procurement Plan Item | Child | Procurement Plan | No  | Procurement Officer | Cost aggregation |

Logic example:

total_budget = sum(procurement_plan_items.estimated_cost)

**Step 3 — Procurement Initiation Layer**

1.  Purchase Requisition
2.  Requisition Item

|     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- |
| DocType | Type | Parent | Workflow | Permissions | Custom Logic |
| Purchase Requisition | Transaction | —   | Yes | Department Officer / Finance / Procurement | Budget validation |
| Requisition Item | Child | Purchase Requisition | No  | Department Officer | Auto total calculation |

Validation rules:

estimated_cost > 0  
procurement_plan_item must exist

**Step 4 — Supplier Registry**

1.  Supplier Profile
2.  Supplier Compliance Document

|     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- |
| DocType | Type | Parent | Workflow | Permissions | Custom Logic |
| Supplier Profile | Master | —   | Yes | Supplier / Procurement Officer | Supplier code generation |
| Supplier Compliance Document | Child | Supplier Profile | No  | Supplier | Expiry monitoring |

Automation needed:

Daily job to check expiring compliance documents

**Step 5 — Tender Management**

1.  Tender
2.  Tender Lot
3.  Tender Document

|     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- |
| DocType | Type | Parent | Workflow | Permissions | Custom Logic |
| Tender | Transaction | —   | Yes | Procurement Officer | Generate tender number |
| Tender Lot | Child | Tender | No  | Procurement Officer | Value aggregation |
| Tender Document | Child | Tender | No  | Procurement Officer | Version control |

Important logic:

Once **Published** prevent edit lock documents

**Step 6 — Bidding**

1.  Bid Submission
2.  Bid Document

|     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- |
| DocType | Type | Parent | Workflow | Permissions | Custom Logic |
| Bid Submission | Transaction | —   | Yes | Supplier | Deadline enforcement |
| Bid Document | Child | Bid Submission | No  | Supplier | Hash file |

Critical logic:

submission_time <= submission_deadline

Deadline automation:

Lock all bids at submission_deadline

**Step 7 — Evaluation**

1.  Evaluation Committee
2.  Evaluation Scorecard

|     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- |
| DocType | Type | Parent | Workflow | Permissions | Custom Logic |
| Evaluation Committee | Transaction | Tender | Yes | Procurement Manager | COI declaration |
| Evaluation Scorecard | Transaction | —   | Yes | Committee Member | Score calculation |

Score calculation example:

weighted_score = score \* criteria_weight

**Step 8 — Award**

1.  Award Decision

|     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- |
| DocType | Type | Parent | Workflow | Permissions | Custom Logic |
| Award Decision | Transaction | —   | Yes | Accounting Officer | Notification automation |

Automation:

notify all bidders  
generate award notice

**Step 9 — Reference Tables (Configuration)**

These should be **reference DocTypes**.

|     |     |     |
| --- | --- | --- |
| DocType | Type | Workflow |
| Procurement Method | Reference | No  |
| Supplier Category | Reference | No  |
| Funding Source | Reference | No  |
| Evaluation Criteria | Reference | No  |
| Sector | Reference | No  |

Reason:  
These should **never be hardcoded in scripts**.

### UI and Screen Architecture

1.  **Primary User Groups**

The UI should be organized by **role-based workspaces**.

|     |     |
| --- | --- |
| **Role** | **Main Workspace** |
| Planning Authority | Strategic Planning Workspace |
| Procurement Officer | Procurement Planning Workspace |
| Department Officer | Requisition Workspace |
| Finance Officer | Budget Control Workspace |
| Supplier | Supplier Portal |
| Accounting Officer | Executive Dashboard |
| Auditor | Audit & Monitoring |

1.  **Main Navigation Structure**

Top-level modules:

- Strategic Planning
- Procurement Planning
- Requisitions
- Tender Management
- Supplier Portal
- Evaluation
- Award Management
- Reports & Monitoring
- Administration

### Proposed KenTender App Structure

The custom application app should look like this to keep the system maintainable.

### Procurement Lifecycle State Machine

This is slightly different from workflows and defines:

Plan → Requisition → Tender → Bid → Evaluation → Award → Contract

with **all transitions and allowed events**.

It becomes the **master logic controlling the whole platform** and prevents process bypass.

1.  **Procurement Lifecycle Overview**

The lifecycle has **seven major states**.

Strategic Planning  
↓  
Procurement Planning  
↓  
Procurement Initiation  
↓  
Tender Preparation  
↓  
Tendering / Bidding  
↓  
Evaluation  
↓  
Award

In system terms:

Plan → Requisition → Tender → Bid → Evaluation → Award

Each stage **activates specific DocTypes** and **restricts others**.

1.  **Lifecycle State Table**

|     |     |     |
| --- | --- | --- |
| **State** | **Active Entities** | **Responsible Role** |
| Strategic Planning | National Development Plan, Corporate Strategic Plan | Planning Authority |
| Procurement Planning | Procurement Plan | Procurement Officer |
| Procurement Initiation | Purchase Requisition | Department Officer |
| Tender Preparation | Tender Draft | Procurement Officer |
| Tendering | Bid Submission | Supplier |
| Evaluation | Evaluation Committee, Scorecards | Evaluation Committee |
| Award | Award Decision | Accounting Officer |

1.  **Allowed State Transitions**

This is the **heart of the state machine**.

|     |     |     |
| --- | --- | --- |
| **Current State** | **Event** | **Next State** |
| Strategic Planning | Strategic Plan Approved | Procurement Planning |
| Procurement Planning | APP Approved | Procurement Initiation |
| Procurement Initiation | Requisition Approved | Tender Preparation |
| Tender Preparation | Tender Published | Tendering |
| Tendering | Submission Deadline Reached | Evaluation |
| Evaluation | Evaluation Report Submitted | Award |
| Award | Award Approved | Completed |

1.  **Forbidden Transitions**

The system must **block these transitions**.

|     |     |
| --- | --- |
| **Forbidden Transition** | **Reason** |
| Tender Preparation → Award | Evaluation required |
| Tendering → Award | Evaluation required |
| Requisition → Evaluation | Tender must exist |
| Bid Submission → Award | Committee evaluation required |

These should raise **system validation errors**.

1.  **Lifecycle Diagram**

Here is a **visual state machine**.

1.  **Lifecycle Validation Rules**

These should be enforced in server scripts.

**Rule 1 — Requisition Must Belong to Procurement Plan**

purchase_requisition.procurement_plan_item must exist

**Rule 2 — Tender Must Reference Requisition**

tender.purchase_requisition must exist

**Rule 3 — Bids Allowed Only When Tender Published**

if tender.status != Published  
reject bid

**Rule 4 — Evaluation Only After Tender Closed**

evaluation cannot start if submission_deadline not reached

**Rule 5 — Award Only After Evaluation Complete**

evaluation_report.status == Finalized

1.  **Automation Triggers**

These are key lifecycle events.

| **Event** | **System Action** |
| --- | --- |
| Tender Published | Notify suppliers |
| Bid Submitted | Log audit event |
| Submission Deadline | Lock bids |
| Tender Opening | Generate opening register |
| Evaluation Completed | Generate evaluation report |
| Award Approved | Notify bidders |

1.  **Document Locking Rules**

Certain entities become **immutable** at certain stages.

| **Entity** | **Locked When** |
| --- | --- |
| Procurement Plan | Approved |
| Purchase Requisition | Tender Created |
| Tender | Published |
| Bid Submission | Deadline Passed |
| Evaluation Scorecard | Submitted |

This protects procurement integrity.

1.  **Lifecycle State Tracking**

Create a stage field in key DocTypes:

procurement_stage

Possible values:

Planning  
Initiation  
Tendering  
Evaluation  
Award  
Completed

This makes **reporting and dashboards much easier**.

Example query:

show all procurements in evaluation stage

1.  **Audit Trail Integration**

Each lifecycle transition should log an event in:

**Procurement Audit Log**

Example:

|     |     |
| --- | --- |
| **Event** | **User** |
| Requisition Submitted | dept_user |
| Tender Published | procurement_officer |
| Bid Submitted | supplier |
| Evaluation Submitted | committee_chair |
| Award Approved | accounting_officer |

1.  **Lifecycle SLA Monitoring**

Track **time spent in each stage**.

Example fields:

stage_start_time  
stage_end_time  
stage_duration

Example KPIs:

|     |     |
| --- | --- |
| **KPI** | **Target** |
| Requisition Approval | 7 days |
| Tender Preparation | 14 days |
| Evaluation | 21 days |

This supports **procurement performance reporting**.

1.  **Exception Handling**

The lifecycle must support special cases.

**Cancel Procurement**

Tender → Cancelled

Triggers:

- notify suppliers
- log audit event

**Re-Tender**

If evaluation fails:

Evaluation → Tender Preparation

Create a **new tender version**.

1.  **Procurement Dashboard Metrics**

The lifecycle enables powerful reporting:

Examples:

|     |     |
| --- | --- |
| **Metric** | **Meaning** |
| Active Tenders | currently open |
| Average Evaluation Time | efficiency |
| Supplier Participation | competitiveness |
| Award Rate | procurement success |

1.  **KenTender Logic**

This lifecycle logic should live in the custom app:

kentender.procurement.lifecycle

Functions:

validate_transition()  
trigger_events()  
lock_documents()  
update_stage()

# Role–Permission Matrix

### Roles Definition

|     |     |
| --- | --- |
| Role | Purpose |
| System Administrator | System configuration |
| Planning Authority | Manage national and strategic plans |
| Procurement Officer | Manage procurement planning and tenders |
| Department Officer | Create purchase requisitions |
| Head of Department | Approve requisitions |
| Finance Officer | Validate budget availability |
| Procurement Manager | Approves tenders and manages procurement process |
| Supplier | Register and submit bids |
| Evaluation Committee Member | Score bids |
| Evaluation Committee Chair | Consolidate evaluation |
| Accounting Officer | Final approval of award |
| Auditor | Read-only oversight |

### Permission Levels

|     |     |
| --- | --- |
| Level | Purpose |
| 0   | Basic access |
| 1   | Department approval |
| 2   | Finance review |
| 3   | Procurement review |
| 4   | Evaluation access |
| 5   | Award approval |

This allows **fields to appear only at certain workflow stages**.

Example:

estimated_cost → level 0  
finance_validation → level 2  
award_decision → level 5

### Full Permission Matrix

1.  **Strategic Planning**

|     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| **DocType** | **Role** | **Read** | **Write** | **Create** | **Submit** | **Approve** |
| National Development Plan | Planning Authority | ✓   | ✓   | ✓   | ✓   | ✓   |
| National Development Plan | Auditor | ✓   |     |     |     |     |
| Corporate Strategic Plan | Planning Authority | ✓   | ✓   | ✓   | ✓   | ✓   |
| Corporate Strategic Plan | Auditor | ✓   |     |     |     |     |
| Strategic Objective | Planning Authority | ✓   | ✓   | ✓   |     |     |

1.  **Procurement Planning**

|     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| **DocType** | **Role** | **Read** | **Write** | **Create** | **Submit** | **Approve** |
| Procurement Plan | Procurement Officer | ✓   | ✓   | ✓   | ✓   |     |
| Procurement Plan | Procurement Manager | ✓   | ✓   |     | ✓   | ✓   |
| Procurement Plan | Accounting Officer | ✓   |     |     |     | ✓   |
| Procurement Plan | Auditor | ✓   |     |     |     |     |

1.  **Procurement Initiation**

|     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| **DocType** | **Role** | **Read** | **Write** | **Create** | **Submit** | **Approve** |
| Purchase Requisition | Department Officer | ✓   | ✓   | ✓   | ✓   |     |
| Purchase Requisition | Head of Department | ✓   |     |     |     | ✓   |
| Purchase Requisition | Finance Officer | ✓   | ✓   |     |     | ✓   |
| Purchase Requisition | Procurement Officer | ✓   |     |     |     | ✓   |

1.  **Supplier Registry**

|     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| **DocType** | **Role** | **Read** | **Write** | **Create** | **Submit** | **Approve** |
| Supplier Profile | Supplier | ✓   | ✓   | ✓   | ✓   |     |
| Supplier Profile | Procurement Officer | ✓   | ✓   |     |     | ✓   |
| Supplier Profile | Auditor | ✓   |     |     |     |     |

1.  **Tender Management**

|     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| **DocType** | **Role** | **Read** | **Write** | **Create** | **Submit** | **Approve** |
| Tender | Procurement Officer | ✓   | ✓   | ✓   | ✓   |     |
| Tender | Procurement Manager | ✓   | ✓   |     |     | ✓   |
| Tender | Accounting Officer | ✓   |     |     |     |     |
| Tender | Supplier | ✓   |     |     |     |     |
| Tender | Auditor | ✓   |     |     |     |     |

1.  **Bidding**

|     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| **DocType** | **Role** | **Read** | **Write** | **Create** | **Submit** | **Approve** |
| Bid Submission | Supplier | ✓   | ✓   | ✓   | ✓   |     |
| Bid Submission | Procurement Manager | ✓   |     |     |     |     |
| Bid Submission | Evaluation Committee | ✓   |     |     |     |     |
| Bid Submission | Auditor | ✓   |     |     |     |     |

Important rule:

Suppliers must **only see their own bids**.

1.  **Evaluation**

|     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| **DocType** | **Role** | **Read** | **Write** | **Create** | **Submit** | **Approve** |
| Evaluation Committee | Procurement Manager | ✓   | ✓   | ✓   |     |     |
| Evaluation Scorecard | Committee Member | ✓   | ✓   | ✓   | ✓   |     |
| Evaluation Scorecard | Committee Chair | ✓   | ✓   |     | ✓   | ✓   |
| Evaluation Scorecard | Auditor | ✓   |     |     |     |     |

1.  **Award**

|     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| **DocType** | **Role** | **Read** | **Write** | **Create** | **Submit** | **Approve** |
| Award Decision | Procurement Manager | ✓   | ✓   | ✓   | ✓   |     |
| Award Decision | Accounting Officer | ✓   |     |     |     | ✓   |
| Award Decision | Auditor | ✓   |     |     |     |     |

### Special Restrictions

Certain data must be **hidden until specific workflow stages**.

**Bid Prices**

Visible only after **Tender Opening**.

Field permission:

bid_amount → level 4

**Evaluation Scores**

Visible only to **evaluation committee**.

score → level 4

**Award Decision**

Visible only after **approval**.

award_amount → level 5

**5\. Record-Level Restrictions**

KenTender permission queries should enforce:

**Suppliers**

supplier == current_user_supplier

This ensures suppliers see **only their bids**.

**Evaluation Committee**

Members see only:

tender assigned to them

**6\. Critical Procurement Security Rules**

These must be implemented via **server scripts**.

**Rule 1 — No Self Approval**

requester != approver

**Rule 2 — Tender Lock After Publication**

if status == Published:  
prevent_edit()

**Rule 3 — Bid Deadline Enforcement**

submission_time <= submission_deadline

**Rule 4 — Conflict of Interest**

Committee members must submit:

conflict_of_interest_declaration

before accessing bids.

**7\. Auditor Access**

Auditors must have **read access to everything** except:

- supplier passwords
- encrypted documents

Auditors should also access:

- Procurement Audit Log
- Evaluation Reports
- Award Decisions

**8\. Two Roles to be added later**

Prepare for.

**Appeals Authority**

Handles procurement disputes.

**Public Portal User**

Allows public access to:

- published tenders
- award notices

**9\. KenTender Configuration**

Instead of assigning permissions directly to users, assign them through:

Role → Role Profile → User

Example:

Role Profile:

Procurement Officer  
Roles:

Procurement Officer

Tender Manager

Requisition Reviewer

This simplifies management.