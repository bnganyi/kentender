# KenTender

## Phase 2: Contract Management (Wave 1) — Functional Requirements Specification

# 1\. Introduction

This document defines the Functional Requirements Specification (FRS) for **Phase 2 – Contract Management** of the KenTender electronic procurement platform.

Phase 2 governs the **post-award lifecycle of public procurement contracts**, from contract execution through implementation, monitoring, payment, dispute management, and contract close‑out.

The system must support transparency, accountability, auditability, and compliance with public procurement regulations.

# 2\. Scope of Phase 2

Phase 2 covers the full **contract lifecycle after tender award**, including:

• Contract preparation and signing  
• Contract implementation management  
• Milestone monitoring  
• Inspection and acceptance processes  
• Certification workflows  
• Invoice and payment processing  
• Retention management  
• Claims and dispute handling  
• Contract variations and amendments  
• Contract termination  
• Contract close‑out  
• Defect liability period management

The system shall maintain a complete **audit trail** for all contract activities.

# 3\. Key Actors / Roles

The system shall support the following actors:

**Head of Procurement**  
Responsible for contract preparation, oversight, monitoring, and certification coordination.

**Accounting Officer**  
Approves contracts, appoints implementation teams, issues final acceptance, and authorizes termination.

**Contract Implementation Team (CIT)**  
Responsible for supervising contract implementation and milestone verification.

**Inspection and Acceptance Committee**  
Responsible for testing and validating delivered goods, works, or services.

**Head of User Department**  
Confirms technical compliance and issues certificates of conformance.

**Head of Finance**  
Responsible for payment verification and financial processing.

**Supplier / Contractor**  
Executes the contract and submits deliverables and invoices.

**System Administrator**  
Maintains system configuration and security.

# 4\. Functional Requirements

## 4.1 Contract Preparation

The system shall allow the **Head of Procurement** to prepare a contract agreement following tender award.

System capabilities:

• Automatically import awarded tender data  
• Auto‑populate supplier details  
• Auto‑populate contract value and milestones  
• Generate contract agreement templates  
• Support document attachments  
• Maintain version control

Output:

Contract record ready for signing.

## 4.2 Contract Execution and Signing

The system shall support electronic execution of contracts.

Workflow:

1.  Supplier receives notification to sign contract
2.  Supplier electronically signs contract
3.  Procuring entity receives notification
4.  Accounting Officer signs contract electronically

System requirements:

• Digital signature capability  
• Time‑stamped audit logs  
• Automatic contract activation after signing

## 4.3 Contract Implementation Team (CIT)

The system shall allow the **Accounting Officer** to appoint a Contract Implementation Team.

Members are recommended by the Head of Procurement.

The system shall capture:

• Member name  
• Role  
• Department  
• Qualifications  
• Member type

Member types may include:

• Chairperson  
• Member  
• Secretary  
• Non‑member advisor

## 4.4 Contract Implementation Activities

The system shall support implementation activities depending on contract type.

### Works Contracts

Activities include:

• Site handover procedures  
• Site meetings  
• Meeting minutes (MoM)  
• Milestone verification

### Goods Contracts

Activities include:

• Delivery confirmation  
• Technical testing  
• Milestone verification

All activities must be logged in the system.

## 4.5 Milestone Monitoring

Each contract shall contain predefined milestones.

Milestone attributes:

• Description  
• Expected completion date  
• Deliverables  
• Payment percentage  
• Acceptance criteria

Upon completion:

• CIT records milestone completion minutes • Supplier confirmation is captured

## 4.6 Inspection and Acceptance

The system shall allow the **Head of Procurement** to recommend members for the Inspection and Acceptance Committee.

The system shall capture:

• Member name  
• Role  
• Qualification  
• Department

Optional participants:

• Secretary  
• Technical specialists

## 4.7 Inspection Testing

The system shall allow definition of inspection test plans before milestone completion.

Test attributes:

• Test description  
• Expected results  
• Responsible tester

After inspection, the committee records:

• Inspection minutes  
• Test results  
• Acceptance decision

Possible outcomes:

• Interim acceptance  
• Rejection  
• Penalty recommendation

For goods delivery, the system generates **Goods Received Notes (GRNs)**.

## 4.8 Certification

The system shall generate several certificates during contract execution.

### Interim Acceptance Certificate

Issued following milestone completion.

### Certificate of Conformance

Issued by Head of User Department for complex works or goods.

### Certificate of Acceptance

Issued by Head of Procurement for non‑technical deliveries.

### Final Acceptance Certificate (FAC)

Issued by Accounting Officer upon final delivery.

The FAC triggers final payment processing.

## 4.9 Invoice Submission

Suppliers shall submit invoices through the system.

Invoice data captured:

• Contract reference  
• Milestone reference  
• Invoice amount  
• Tax amount  
• Supporting documentation

## 4.10 Payment Processing

Payment workflow:

1.  Supplier submits invoice
2.  Head of Procurement reviews invoice
3.  Invoice forwarded to Head of Finance
4.  System generates payment voucher template
5.  Head of Finance verifies payment
6.  Head of Procurement certifies voucher
7.  Finance processes payment and posts to GL

System shall support partial and final payments.

## 4.11 Statutory Compliance

The system shall support statutory deductions and tax reporting.

Capabilities include:

• Integration with electronic tax register systems  
• Automatic calculation of statutory deductions

## 4.12 Retention Management

The system shall support retention deductions from payments.

Capabilities include:

• Track retention balances  
• Schedule retention release  
• Send reminders when retention periods expire  
• Allow deductions during retention period

## 4.13 Contract Monitoring

The Head of Procurement shall prepare monthly contract monitoring reports.

Reports shall include:

• Milestone progress  
• Payment status  
• Outstanding obligations  
• Contract risks

## 4.14 Claims Management

### Claims by Procuring Entity

The system shall support claims including:

• Liquidated damages  
• Performance penalties

The system shall automatically calculate penalties where applicable.

### Claims by Contractor

Contractors may submit claims such as:

• Interest on delayed payments  
• Compensation claims  
• Variation claims

## 4.15 Dispute Management

The system shall support dispute lifecycle management.

Stages include:

1.  Notice of claim  
    
2.  Negotiation  
    
3.  Mediation  
    
4.  Arbitration

The Accounting Officer may issue **Stop Work Orders** based on advice from the CIT and Head of Procurement.

## 4.16 Contract Variations

The system shall support contract amendments.

Variation types:

• Scope change  
• Time extension  
• Cost adjustment

Each variation must include:

• Justification  
• Approval workflow  
• Financial impact

## 4.17 Contract Termination

The Accounting Officer may terminate contracts based on legal advice.

Termination workflow includes:

• Notice issued to supplier  
• Settlement of accounts  
• Site or property handover  
• Discharge documentation

The system shall record:

• Termination reason  
• Supporting documents  
• Final financial reconciliation

## 4.18 Contract Close‑Out

Contract close‑out occurs when:

• Final Acceptance Certificate issued  
• All payments completed  
• Goods or works handed over

The system shall archive the contract record.

## 4.19 Defect Liability Period

After handover, the system shall manage the Defect Liability Period (DLP).

Capabilities include:

• Track DLP duration  
• Record defect notifications  
• Allow contract reopening if defects arise

# 5\. Business Rules

• Contracts cannot become active before electronic signing.  
• Payments cannot be processed without a valid certificate.  
• Final payment requires issuance of Final Acceptance Certificate.  
• Retention funds must remain locked until retention period ends unless deductions are applied.  
• Contract termination requires Accounting Officer approval and documented justification.

# 6\. ERPNext Data Model

The system shall implement the following primary DocTypes.

Core entities:

• Contract  
• Contract Milestone  
• Contract Implementation Team  
• Inspection Committee  
• Inspection Test Plan  
• Inspection Report  
• Acceptance Certificate  
• Supplier Invoice  
• Payment Voucher  
• Retention Ledger  
• Contract Variation  
• Claim  
• Dispute Case  
• Termination Record  
• Defect Liability Case

# 7\. Key Entity Relationships

Tender → Contract

Contract → Milestones

Contract → CIT Members

Contract → Inspection Committee

Milestone → Inspection Report

Inspection Report → Certificate

Certificate → Invoice

Invoice → Payment Voucher

Contract → Variations

Contract → Claims

Contract → Disputes

Contract → Termination

Contract → Defect Liability

# 8\. Reporting Requirements

The system shall generate the following reports.

• Contract Status Dashboard  
• Milestone Tracking Report  
• Payment Progress Report  
• Retention Schedule Report  
• Claims Register  
• Dispute Register  
• Contract Close‑Out Report

# 9\. Integration Requirements

The system should support integration with external government systems including:

• Financial management systems  
• Electronic tax systems  
• Treasury payment platforms

All integrations must support secure APIs and audit logging.