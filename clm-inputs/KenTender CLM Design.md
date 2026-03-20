# KENTENDER CONTRACT LIFECYCLE MANAGEMENT

**🧱 KENTENDER CLM — INTEGRATION BLUEPRINT**

**🎯 Core Principle (this governs everything)**

| **Layer** | **Responsibility** |
| --- | --- |
| ERPNext Core | Execution, finance, inventory, quality |
| KenTender (Custom) | Governance, compliance, legal control |

**📜 1. CONTRACT PREPARATION & SIGNING**

**Requirement:**

Contract creation, templates, signing, activation

**Mapping:**

| **Function** | **System** |
| --- | --- |
| Contract record | ✅ Custom (Contract DocType) |
| Supplier, value | ✅ From Tender / PO |
| Document templates | ERPNext Print Format |
| Digital signature | ⚠️ Extend (custom or integration) |

**Integration:**

Tender → Contract (custom)  
Contract → Purchase Order (ERPNext)

**Rule:**

- Contract becomes **Active only after signing**

**👥 2. CONTRACT IMPLEMENTATION TEAM (CIT)**

**Requirement:**

Structured team with roles, qualifications

**Mapping:**

| **Function** | **System** |
| --- | --- |
| Members | ERPNext Employee |
| Department | ERPNext Department |
| Roles | ERPNext Role |
| Assignment | ✅ Custom (link table) |

**Final Design:**

- Use Employee (not User directly)
- Custom child table = assignment only

**🏗️ 3. IMPLEMENTATION & ACTIVITIES**

**Requirement:**

Site meetings, delivery, tracking

**Mapping:**

| **Function** | **System** |
| --- | --- |
| Contract execution | Project |
| Activities | Task |
| Meetings / logs | Task comments / custom logs |

**Rule:**

- Contract MUST create Project automatically

**🎯 4. MILESTONE MONITORING**

**Requirement:**

Milestones with deliverables + payment %

**Mapping:**

| **Function** | **System** |
| --- | --- |
| Milestones | Task |
| Deliverables | Task description |
| Dates | Task dates |
| Payment % | ⚠️ Custom field on Task |

**Important:**

👉 Do NOT create separate Milestone DocType  
Use Task + custom fields

**🔬 5. INSPECTION & TESTING**

**Requirement:**

Test plans, inspection, acceptance decisions

**Mapping:**

| **Function** | **System** |
| --- | --- |
| Test definition | Quality Inspection Template |
| Execution | Quality Inspection |
| Result | Built-in |

**For goods:**

- Trigger from:
    - Purchase Receipt

**📜 6. CERTIFICATION (CUSTOM — CORE GAP)**

**Requirement:**

4 certificate types (Interim, Conformance, Acceptance, Final)

**Mapping:**

| **Function** | **System** |
| --- | --- |
| Certificates | ✅ Custom |
| Link to milestone | Task |
| Link to inspection | Quality Inspection |

**Critical Rule:**

- Certificate is REQUIRED before invoice

**💰 7. INVOICE & PAYMENT**

**Requirement:**

Full financial workflow

**Mapping:**

| **Function** | **System** |
| --- | --- |
| Invoice | Purchase Invoice |
| Payment | Payment Entry |
| GL Posting | ERPNext |

**Enforcement:**

Certificate → Invoice → Payment

**🧮 8. RETENTION MANAGEMENT (CUSTOM)**

**Requirement:**

Retention tracking, release, deductions

**Mapping:**

| **Function** | **System** |
| --- | --- |
| Retention tracking | ✅ Custom |
| Payment deduction | Hook into Purchase Invoice |
| Release | Scheduled logic |

**📊 9. CONTRACT MONITORING**

**Requirement:**

Monthly reports, status tracking

**Mapping:**

| **Function** | **System** |
| --- | --- |
| Progress | Project |
| Milestones | Task |
| Payments | Purchase Invoice |
| Dashboard | ERPNext Dashboard |

**⚖️ 10. CLAIMS & DISPUTES (CUSTOM)**

**Requirement:**

Full lifecycle legal management

**Mapping:**

| **Function** | **System** |
| --- | --- |
| Claims | ✅ Custom |
| Disputes | ✅ Custom |
| Workflow | Custom |

**🔄 11. VARIATIONS**

**Requirement:**

Scope, time, cost adjustments

**Mapping:**

| **Function** | **System** |
| --- | --- |
| Variation record | ✅ Custom |
| Cost impact | Update PO |
| Time impact | Update Project/Task |

**❌ 12. TERMINATION**

**Requirement:**

Legal termination workflow

**Mapping:**

| **Function** | **System** |
| --- | --- |
| Termination record | ✅ Custom |
| Financial closure | ERPNext |
| Audit trail | Both |

**📦 13. CLOSE-OUT**

**Requirement:**

Final acceptance, archive

**Mapping:**

| **Function** | **System** |
| --- | --- |
| Final Acceptance Certificate | Custom |
| Final Payment | ERPNext |
| Archive | Status + docstate |

**🔧 14. DEFECT LIABILITY PERIOD (DLP)**

**Requirement:**

Post-delivery defect tracking

**Mapping:**

| **Function** | **System** |
| --- | --- |
| DLP tracking | ✅ Custom |
| Issues | Could extend Quality or custom |

**🔗 FINAL SYSTEM MAP (SIMPLIFIED)**

Tender  
↓  
Contract (Custom)  
↓  
Project (ERPNext)  
↓  
Task (Milestones)  
↓  
Quality Inspection (ERPNext)  
↓  
Certificate (Custom)  
↓  
Purchase Invoice (ERPNext)  
↓  
Payment Entry (ERPNext)

**⚠️ CRITICAL DESIGN RULES (NON-NEGOTIABLE)**

1.  Never duplicate ERPNext functionality
2.  Always link—not copy—data
3.  Use ERPNext workflows where possible
4.  Keep custom layer thin but authoritative

**🧠 WHAT YOU JUST BUILT (IMPORTANT)**

This blueprint ensures:

- Zero duplication
- Maximum ERPNext leverage
- Clean upgrade path
- Audit-ready architecture

**A. Final ERP-aligned CLM DocTypes**

**1) Contract**

This is the master governance record. It should not duplicate Purchase Order, Project, or Supplier data unnecessarily.

{  
"doctype": "DocType",  
"name": "Contract",  
"module": "KenTender",  
"custom": 1,  
"is_submittable": 1,  
"fields": \[  
{ "fieldname": "contract_title", "fieldtype": "Data", "reqd": 1 },  
{ "fieldname": "company", "fieldtype": "Link", "options": "Company", "reqd": 1 },  
{ "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "reqd": 1 },  
{ "fieldname": "tender", "fieldtype": "Link", "options": "Tender", "reqd": 1 },  
{ "fieldname": "purchase_order", "fieldtype": "Link", "options": "Purchase Order" },  
{ "fieldname": "project", "fieldtype": "Link", "options": "Project" },  
{ "fieldname": "contract_type", "fieldtype": "Select", "options": "Goods\\nWorks\\nServices", "reqd": 1 },  
{ "fieldname": "contract_value", "fieldtype": "Currency", "reqd": 1 },  
{ "fieldname": "currency", "fieldtype": "Link", "options": "Currency", "reqd": 1 },  
{ "fieldname": "start_date", "fieldtype": "Date" },  
{ "fieldname": "end_date", "fieldtype": "Date" },  
{ "fieldname": "status", "fieldtype": "Select", "options": "Draft\\nPending Signature\\nActive\\nSuspended\\nTerminated\\nClosed", "reqd": 1 },  
{ "fieldname": "signed_by_supplier", "fieldtype": "Check" },  
{ "fieldname": "signed_by_accounting_officer", "fieldtype": "Check" },  
{ "fieldname": "activated_on", "fieldtype": "Datetime" },  
{ "fieldname": "retention_percentage", "fieldtype": "Percent" },  
{ "fieldname": "defect_liability_months", "fieldtype": "Int" },  
{ "fieldname": "final_acceptance_certificate", "fieldtype": "Link", "options": "Acceptance Certificate" }  
\]  
}

**2) Contract Implementation Team Member**

This should be an assignment layer, not a reinvention of employee master data.

{  
"doctype": "DocType",  
"name": "Contract Implementation Team Member",  
"module": "KenTender",  
"custom": 1,  
"fields": \[  
{ "fieldname": "contract", "fieldtype": "Link", "options": "Contract", "reqd": 1 },  
{ "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "reqd": 1 },  
{ "fieldname": "member_type", "fieldtype": "Select", "options": "Chairperson\\nMember\\nSecretary\\nNon-member Advisor", "reqd": 1 },  
{ "fieldname": "role_in_team", "fieldtype": "Data" },  
{ "fieldname": "department", "fieldtype": "Link", "options": "Department" },  
{ "fieldname": "qualification", "fieldtype": "Data" },  
{ "fieldname": "appointed_by", "fieldtype": "Link", "options": "User" },  
{ "fieldname": "appointed_on", "fieldtype": "Datetime" },  
{ "fieldname": "status", "fieldtype": "Select", "options": "Proposed\\nApproved\\nActive\\nRemoved", "reqd": 1 }  
\]  
}

**3) Inspection Committee Member**

Same principle. Use Employee and Department from ERPNext/Frappe HR.

{  
"doctype": "DocType",  
"name": "Inspection Committee Member",  
"module": "KenTender",  
"custom": 1,  
"fields": \[  
{ "fieldname": "contract", "fieldtype": "Link", "options": "Contract", "reqd": 1 },  
{ "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "reqd": 1 },  
{ "fieldname": "member_type", "fieldtype": "Select", "options": "Chairperson\\nMember\\nSecretary\\nTechnical Specialist", "reqd": 1 },  
{ "fieldname": "department", "fieldtype": "Link", "options": "Department" },  
{ "fieldname": "qualification", "fieldtype": "Data" },  
{ "fieldname": "appointed_by", "fieldtype": "Link", "options": "User" },  
{ "fieldname": "appointed_on", "fieldtype": "Datetime" },  
{ "fieldname": "status", "fieldtype": "Select", "options": "Proposed\\nApproved\\nActive\\nRemoved", "reqd": 1 }  
\]  
}

**4) Acceptance Certificate**

This remains custom because ERPNext does not model your required public-procurement certificate types.

{  
"doctype": "DocType",  
"name": "Acceptance Certificate",  
"module": "KenTender",  
"custom": 1,  
"is_submittable": 1,  
"fields": \[  
{ "fieldname": "certificate_type", "fieldtype": "Select", "options": "Interim Acceptance\\nCertificate of Conformance\\nCertificate of Acceptance\\nFinal Acceptance", "reqd": 1 },  
{ "fieldname": "contract", "fieldtype": "Link", "options": "Contract", "reqd": 1 },  
{ "fieldname": "project", "fieldtype": "Link", "options": "Project" },  
{ "fieldname": "task", "fieldtype": "Link", "options": "Task" },  
{ "fieldname": "quality_inspection", "fieldtype": "Link", "options": "Quality Inspection" },  
{ "fieldname": "purchase_receipt", "fieldtype": "Link", "options": "Purchase Receipt" },  
{ "fieldname": "issued_by", "fieldtype": "Link", "options": "User", "reqd": 1 },  
{ "fieldname": "issued_on", "fieldtype": "Datetime", "reqd": 1 },  
{ "fieldname": "decision", "fieldtype": "Select", "options": "Approved\\nRejected\\nConditional", "reqd": 1 },  
{ "fieldname": "remarks", "fieldtype": "Small Text" },  
{ "fieldname": "certificate_reference", "fieldtype": "Data", "unique": 1 }  
\]  
}

**5) Retention Ledger**

ERPNext can handle accounting, but retention control per contract is still your custom governance layer.

{  
"doctype": "DocType",  
"name": "Retention Ledger",  
"module": "KenTender",  
"custom": 1,  
"fields": \[  
{ "fieldname": "contract", "fieldtype": "Link", "options": "Contract", "reqd": 1 },  
{ "fieldname": "purchase_invoice", "fieldtype": "Link", "options": "Purchase Invoice" },  
{ "fieldname": "payment_entry", "fieldtype": "Link", "options": "Payment Entry" },  
{ "fieldname": "retention_type", "fieldtype": "Select", "options": "Deduction\\nRelease\\nAdjustment", "reqd": 1 },  
{ "fieldname": "posting_date", "fieldtype": "Date", "reqd": 1 },  
{ "fieldname": "amount", "fieldtype": "Currency", "reqd": 1 },  
{ "fieldname": "balance_after_transaction", "fieldtype": "Currency" },  
{ "fieldname": "release_date", "fieldtype": "Date" },  
{ "fieldname": "status", "fieldtype": "Select", "options": "Pending\\nHeld\\nReleased\\nAdjusted", "reqd": 1 },  
{ "fieldname": "remarks", "fieldtype": "Small Text" }  
\]  
}

**6) Contract Variation**

This should govern amendment logic and then drive updates to PO, Project, Task dates, and contract value.

{  
"doctype": "DocType",  
"name": "Contract Variation",  
"module": "KenTender",  
"custom": 1,  
"is_submittable": 1,  
"fields": \[  
{ "fieldname": "contract", "fieldtype": "Link", "options": "Contract", "reqd": 1 },  
{ "fieldname": "variation_type", "fieldtype": "Select", "options": "Scope Change\\nTime Extension\\nCost Adjustment", "reqd": 1 },  
{ "fieldname": "justification", "fieldtype": "Small Text", "reqd": 1 },  
{ "fieldname": "financial_impact", "fieldtype": "Currency" },  
{ "fieldname": "time_extension_days", "fieldtype": "Int" },  
{ "fieldname": "revised_contract_value", "fieldtype": "Currency" },  
{ "fieldname": "revised_end_date", "fieldtype": "Date" },  
{ "fieldname": "status", "fieldtype": "Select", "options": "Draft\\nUnder Review\\nApproved\\nRejected\\nImplemented", "reqd": 1 },  
{ "fieldname": "approved_by", "fieldtype": "Link", "options": "User" },  
{ "fieldname": "approved_on", "fieldtype": "Datetime" }  
\]  
}

**7) Claim**

Keep this custom. ERPNext does not provide procurement-legal claim lifecycle management.

{  
"doctype": "DocType",  
"name": "Claim",  
"module": "KenTender",  
"custom": 1,  
"is_submittable": 1,  
"fields": \[  
{ "fieldname": "contract", "fieldtype": "Link", "options": "Contract", "reqd": 1 },  
{ "fieldname": "claim_by", "fieldtype": "Select", "options": "Procuring Entity\\nSupplier", "reqd": 1 },  
{ "fieldname": "claim_type", "fieldtype": "Select", "options": "Liquidated Damages\\nPerformance Penalty\\nInterest on Delayed Payment\\nCompensation Claim\\nVariation Claim\\nOther", "reqd": 1 },  
{ "fieldname": "claim_date", "fieldtype": "Date", "reqd": 1 },  
{ "fieldname": "amount", "fieldtype": "Currency" },  
{ "fieldname": "description", "fieldtype": "Small Text", "reqd": 1 },  
{ "fieldname": "status", "fieldtype": "Select", "options": "Draft\\nSubmitted\\nUnder Review\\nApproved\\nRejected\\nSettled", "reqd": 1 },  
{ "fieldname": "reference_variation", "fieldtype": "Link", "options": "Contract Variation" }  
\]  
}

**8) Dispute Case**

This is a distinct lifecycle from claims, and your FRS explicitly requires staged handling.

{  
"doctype": "DocType",  
"name": "Dispute Case",  
"module": "KenTender",  
"custom": 1,  
"is_submittable": 1,  
"fields": \[  
{ "fieldname": "contract", "fieldtype": "Link", "options": "Contract", "reqd": 1 },  
{ "fieldname": "claim", "fieldtype": "Link", "options": "Claim" },  
{ "fieldname": "notice_date", "fieldtype": "Date", "reqd": 1 },  
{ "fieldname": "current_stage", "fieldtype": "Select", "options": "Notice of Claim\\nNegotiation\\nMediation\\nArbitration", "reqd": 1 },  
{ "fieldname": "status", "fieldtype": "Select", "options": "Open\\nIn Progress\\nResolved\\nClosed", "reqd": 1 },  
{ "fieldname": "stop_work_order_issued", "fieldtype": "Check" },  
{ "fieldname": "issued_by", "fieldtype": "Link", "options": "User" },  
{ "fieldname": "summary", "fieldtype": "Small Text" },  
{ "fieldname": "resolution", "fieldtype": "Small Text" }  
\]  
}

**9) Termination Record**

Needs to capture legal justification and financial reconciliation without duplicating accounting entries.

{  
"doctype": "DocType",  
"name": "Termination Record",  
"module": "KenTender",  
"custom": 1,  
"is_submittable": 1,  
"fields": \[  
{ "fieldname": "contract", "fieldtype": "Link", "options": "Contract", "reqd": 1 },  
{ "fieldname": "termination_date", "fieldtype": "Date", "reqd": 1 },  
{ "fieldname": "termination_reason", "fieldtype": "Small Text", "reqd": 1 },  
{ "fieldname": "approved_by", "fieldtype": "Link", "options": "User", "reqd": 1 },  
{ "fieldname": "settlement_status", "fieldtype": "Select", "options": "Pending\\nIn Progress\\nCompleted", "reqd": 1 },  
{ "fieldname": "final_financial_reconciliation", "fieldtype": "Currency" },  
{ "fieldname": "handover_completed", "fieldtype": "Check" },  
{ "fieldname": "discharge_document_reference", "fieldtype": "Data" }  
\]  
}

**10) Defect Liability Case**

This stays custom. It is not the same as quality inspection. It is post-handover liability tracking.

{  
"doctype": "DocType",  
"name": "Defect Liability Case",  
"module": "KenTender",  
"custom": 1,  
"fields": \[  
{ "fieldname": "contract", "fieldtype": "Link", "options": "Contract", "reqd": 1 },  
{ "fieldname": "project", "fieldtype": "Link", "options": "Project" },  
{ "fieldname": "reported_on", "fieldtype": "Datetime", "reqd": 1 },  
{ "fieldname": "reported_by", "fieldtype": "Link", "options": "User" },  
{ "fieldname": "defect_description", "fieldtype": "Small Text", "reqd": 1 },  
{ "fieldname": "severity", "fieldtype": "Select", "options": "Low\\nMedium\\nHigh\\nCritical", "reqd": 1 },  
{ "fieldname": "status", "fieldtype": "Select", "options": "Open\\nUnder Review\\nAssigned\\nResolved\\nClosed", "reqd": 1 },  
{ "fieldname": "resolution_due_date", "fieldtype": "Date" },  
{ "fieldname": "resolved_on", "fieldtype": "Datetime" },  
{ "fieldname": "contract_reopened", "fieldtype": "Check" }  
\]  
}

**What should not be custom**

These should be reused from ERPNext, not recreated:

- Project
- Task
- Quality Inspection Template
- Quality Inspection
- Purchase Receipt
- Purchase Invoice
- Payment Entry
- Employee
- Department
- Company
- Supplier

**Minimal custom fields to add to ERPNext core DocTypes**

**Task**

Add custom fields to make Task serve as Contract Milestone:

\[  
{ "fieldname": "is_contract_milestone", "fieldtype": "Check" },  
{ "fieldname": "contract", "fieldtype": "Link", "options": "Contract" },  
{ "fieldname": "payment_percentage", "fieldtype": "Percent" },  
{ "fieldname": "acceptance_criteria", "fieldtype": "Small Text" },  
{ "fieldname": "deliverables", "fieldtype": "Small Text" },  
{ "fieldname": "supplier_confirmed", "fieldtype": "Check" },  
{ "fieldname": "milestone_status", "fieldtype": "Select", "options": "Pending\\nCompleted\\nAccepted\\nRejected" }  
\]

**Project**

Add a link back to Contract:

\[  
{ "fieldname": "contract", "fieldtype": "Link", "options": "Contract" }  
\]

**Purchase Invoice**

Add contract/certificate linkage:

\[  
{ "fieldname": "contract", "fieldtype": "Link", "options": "Contract" },  
{ "fieldname": "acceptance_certificate", "fieldtype": "Link", "options": "Acceptance Certificate" },  
{ "fieldname": "milestone_task", "fieldtype": "Link", "options": "Task" }  
\]

**Purchase Receipt**

Add contract/milestone linkage:

\[  
{ "fieldname": "contract", "fieldtype": "Link", "options": "Contract" },  
{ "fieldname": "milestone_task", "fieldtype": "Link", "options": "Task" }  
\]

**System ownership map**

Here is the clean ownership boundary:

| **Area** | **Owner** |
| --- | --- |
| Contract governance | Custom |
| Execution timeline | Project / Task |
| Goods receipt | Purchase Receipt |
| Inspection and testing | Quality |
| Certification | Custom |
| Invoice posting | Purchase Invoice |
| Payment | Payment Entry |
| Retention control | Custom |
| Variations | Custom + hooks into PO/Project |
| Claims / disputes / termination / DLP | Custom |

Locked.

Those three decisions are the right ones for this system and they fit your requirements well:

- **Contract = workflow-controlled master record**, which matches the heavy approval and lifecycle behavior in your CLM requirements.
- **Acceptance Certificate = one DocType with certificate_type**, which fits your requirement for multiple certificate types without fragmenting the model.
- **Retention Ledger = transaction-style with computed summary**, which matches the requirement to track balances, releases, deductions, and reminders without duplicating data.

**Finalized CLM modeling decisions**

**Contract**

- Not submittable
- Controlled by workflow states
- Central governance record over:
    - signing
    - activation
    - suspension
    - termination
    - close-out
- Links outward to ERPNext objects rather than copying them:
    - Project
    - Purchase Order
    - Purchase Invoice
    - Payment Entry

**Acceptance Certificate**

- Single DocType
- certificate_type values:
    - Interim Acceptance
    - Certificate of Conformance
    - Certificate of Acceptance
    - Final Acceptance
- Same approval and audit framework across all certificate types
- Easier reporting and cleaner permissions

**Retention Ledger**

- Pure transaction ledger
- Each row is a financial event:
    - deduction
    - adjustment
    - release
- Contract-level retention position is computed from ledger rows
- Better auditability and avoids reconciliation drift

**What this means structurally**

Your custom CLM layer is now firmly limited to what ERPNext does **not** natively cover:

- Contract governance
- CIT and committee assignment
- Acceptance certificates
- Retention control
- Variations
- Claims
- Disputes
- Termination
- Defect liability

And your ERPNext-native layer remains:

- Project / Task for execution and milestones
- Quality for inspection/testing
- Purchase Receipt for GRN-like receiving
- Purchase Invoice for invoicing
- Payment Entry for disbursement
- Employee / Department / Company / Supplier as masters

That is the correct boundary.

**Next step: B — integration code layer**

Now we should wire the system behavior, specifically these eight integrations:

1.  **Awarded Tender → Contract creation**
2.  **Contract activation → Project creation**
3.  **Contract milestones → Task creation / synchronization**
4.  **Goods milestones → Purchase Receipt linkage**
5.  **Inspection flow → Quality Inspection creation and validation**
6.  **Certificate issuance → Purchase Invoice eligibility**
7.  **Purchase Invoice posting → Retention Ledger transactions**
8.  **Final Acceptance / final payment / DLP start**

**Recommended build order for the integration layer**

**Wave 1**

- Tender → Contract
- Contract → Project
- Contract milestone fields on Task
- Certificate gate before invoice

**Wave 2**

- Purchase Receipt + Quality integration
- Retention posting hooks
- Final acceptance and close-out logic

**Wave 3**

- Variations updating Project / PO / Contract
- DLP automation
- Termination and dispute integration

Here’s the **Phase 3 CLM integration layer**, refactored for tight ERPNext alignment.

**contract_service.py**

import frappe  
from frappe import _  
from frappe.utils import now_datetime, nowdate, add_months  
<br/><br/>def create_contract_from_award(tender_name: str, submission_name: str) -> str:  
tender = frappe.get_doc("Tender", tender_name)  
submission = frappe.get_doc("Tender Submission", submission_name)  
<br/>if tender.status != "Evaluated":  
frappe.throw(\_("Tender must be Evaluated before contract creation."))  
<br/>existing = frappe.db.get_value("Contract", {"tender": tender.name}, "name")  
if existing:  
return existing  
<br/>po_name = create_purchase_order_from_award(tender, submission)  
<br/>contract = frappe.get_doc({  
"doctype": "Contract",  
"contract_title": f"{tender.name} - {submission.supplier}",  
"company": tender.company,  
"supplier": submission.supplier,  
"tender": tender.name,  
"purchase_order": po_name,  
"contract_type": tender.contract_type if hasattr(tender, "contract_type") else "Goods",  
"contract_value": submission.base_amount or submission.quoted_amount,  
"currency": submission.currency,  
"status": "Pending Signature",  
"retention_percentage": getattr(tender, "retention_percentage", 0) or 0,  
"defect_liability_months": getattr(tender, "defect_liability_months", 0) or 0,  
})  
contract.insert(ignore_permissions=True)  
<br/>tender.contract = contract.name  
tender.status = "Awarded"  
tender.save(ignore_permissions=True)  
<br/>contract.add_comment("Comment", \_("Created automatically from tender award."))  
return contract.name  
<br/><br/>def create_purchase_order_from_award(tender, submission) -> str:  
plan_item = frappe.get_doc("Procurement Plan Item", tender.procurement_plan_item)  
<br/>po = frappe.get_doc({  
"doctype": "Purchase Order",  
"supplier": submission.supplier,  
"company": tender.company,  
"currency": submission.currency,  
"conversion_rate": submission.exchange_rate,  
"schedule_date": nowdate(),  
"items": \[  
{  
"item_code": plan_item.item_code,  
"qty": plan_item.qty,  
"rate": submission.quoted_amount,  
"project": None,  
}  
\]  
})  
po.insert(ignore_permissions=True)  
po.submit()  
<br/>return po.name  
<br/><br/>@frappe.whitelist()  
def sign_contract(contract_name: str, signer_role: str) -> None:  
contract = frappe.get_doc("Contract", contract_name)  
<br/>if signer_role == "Supplier":  
contract.signed_by_supplier = 1  
elif signer_role == "Accounting Officer":  
contract.signed_by_accounting_officer = 1  
else:  
frappe.throw(\_("Invalid signer role."))  
<br/>contract.save(ignore_permissions=True)  
contract.add_comment("Comment", \_(f"Signed by {signer_role}: {frappe.session.user}"))  
<br/>if contract.signed_by_supplier and contract.signed_by_accounting_officer:  
activate_contract(contract.name)  
<br/><br/>def activate_contract(contract_name: str) -> None:  
contract = frappe.get_doc("Contract", contract_name)  
<br/>if not contract.signed_by_supplier or not contract.signed_by_accounting_officer:  
frappe.throw(\_("Contract cannot become active before both signatures are completed."))  
<br/>if not contract.project:  
from kentender.project_integration import create_project_for_contract  
project_name = create_project_for_contract(contract.name)  
contract.project = project_name  
<br/>contract.status = "Active"  
contract.activated_on = now_datetime()  
contract.save(ignore_permissions=True)  
contract.add_comment("Comment", \_("Contract activated automatically after signing."))  
<br/><br/>def start_defect_liability_period(contract_name: str) -> None:  
contract = frappe.get_doc("Contract", contract_name)  
<br/>if not contract.defect_liability_months:  
return  
<br/>dlp_end = add_months(nowdate(), int(contract.defect_liability_months))  
contract.db_set("dlp_end_date", dlp_end, update_modified=True)  
contract.add_comment("Comment", \_(f"Defect Liability Period started. Ends on {dlp_end}."))

**project_integration.py**

import frappe  
from frappe import _  
<br/><br/>def create_project_for_contract(contract_name: str) -> str:  
contract = frappe.get_doc("Contract", contract_name)  
<br/>existing = frappe.db.get_value("Project", {"contract": contract.name}, "name")  
if existing:  
return existing  
<br/>project = frappe.get_doc({  
"doctype": "Project",  
"project_name": contract.contract_title,  
"company": contract.company,  
"status": "Open",  
"contract": contract.name,  
})  
project.insert(ignore_permissions=True)  
<br/>contract.add_comment("Comment", \_(f"Project created: {project.name}"))  
return project.name  
<br/><br/>def sync_contract_tasks_from_milestone_template(contract_name: str) -> list\[str\]:  
"""  
Creates Task records from tender/plan-derived milestone definitions.  
Replace the source query below with your final milestone source.  
"""  
contract = frappe.get_doc("Contract", contract_name)  
created = \[\]  
<br/>milestone_rows = get_contract_milestone_source(contract)  
<br/>for row in milestone_rows:  
existing = frappe.db.get_value(  
"Task",  
{"project": contract.project, "subject": row\["description"\]},  
"name"  
)  
if existing:  
continue  
<br/>task = frappe.get_doc({  
"doctype": "Task",  
"project": contract.project,  
"subject": row\["description"\],  
"exp_end_date": row.get("expected_date"),  
"description": row.get("deliverables"),  
"contract": contract.name,  
"is_contract_milestone": 1,  
"payment_percentage": row.get("payment_percentage") or 0,  
"acceptance_criteria": row.get("acceptance_criteria"),  
"deliverables": row.get("deliverables"),  
"milestone_status": "Pending",  
})  
task.insert(ignore_permissions=True)  
created.append(task.name)  
<br/>return created  
<br/><br/>def get_contract_milestone_source(contract) -> list\[dict\]:  
"""  
Placeholder source. Replace with your actual milestone planning source.  
"""  
return \[  
{  
"description": "Initial Delivery",  
"expected_date": contract.start_date,  
"deliverables": "Initial deliverables as per contract",  
"payment_percentage": 40,  
"acceptance_criteria": "Delivered and inspected"  
},  
{  
"description": "Final Delivery",  
"expected_date": contract.end_date,  
"deliverables": "Final deliverables as per contract",  
"payment_percentage": 60,  
"acceptance_criteria": "Final acceptance issued"  
}  
\]

**quality_integration.py**

import frappe  
from frappe import _  
<br/><br/>def create_quality_inspection_for_task(task_name: str, purchase_receipt_name: str | None = None) -> str:  
task = frappe.get_doc("Task", task_name)  
contract = frappe.get_doc("Contract", task.contract)  
<br/>item_code = \_get_contract_item_code(contract)  
<br/>qi = frappe.get_doc({  
"doctype": "Quality Inspection",  
"inspection_type": "Incoming",  
"reference_type": "Task",  
"reference_name": task.name,  
"item_code": item_code,  
"report_date": frappe.utils.nowdate(),  
})  
<br/>if purchase_receipt_name and qi.meta.has_field("purchase_receipt_no"):  
qi.purchase_receipt_no = purchase_receipt_name  
<br/>qi.insert(ignore_permissions=True)  
return qi.name  
<br/><br/>def validate_task_acceptance_ready(task_name: str) -> None:  
task = frappe.get_doc("Task", task_name)  
<br/>qi_name = frappe.db.get_value(  
"Quality Inspection",  
{"reference_type": "Task", "reference_name": task.name},  
"name"  
)  
if not qi_name:  
frappe.throw(\_("Quality Inspection is required before certificate issuance."))  
<br/>qi = frappe.get_doc("Quality Inspection", qi_name)  
<br/>\# Adjust this depending on your ERPNext version/fields.  
accepted = getattr(qi, "status", None) in ("Accepted", "Completed") or getattr(qi, "report_status", None) == "Accepted"  
if not accepted:  
frappe.throw(\_("Quality Inspection must be accepted before certificate issuance."))  
<br/><br/>def \_get_contract_item_code(contract) -> str:  
po = frappe.get_doc("Purchase Order", contract.purchase_order)  
if not po.items:  
frappe.throw(\_("Purchase Order has no items."))  
return po.items\[0\].item_code

**finance_integration.py**

import frappe  
from frappe import _  
from frappe.utils import nowdate  
<br/><br/>def validate_purchase_invoice_certificate(doc, method=None):  
if not doc.contract:  
return  
<br/>if not doc.acceptance_certificate:  
frappe.throw(\_("Purchase Invoice requires a valid Acceptance Certificate."))  
<br/>cert = frappe.get_doc("Acceptance Certificate", doc.acceptance_certificate)  
<br/>if cert.docstatus != 1:  
frappe.throw(\_("Acceptance Certificate must be submitted."))  
<br/>if cert.decision != "Approved":  
frappe.throw(\_("Only approved certificates can support invoice processing."))  
<br/>if cert.contract != doc.contract:  
frappe.throw(\_("Acceptance Certificate does not belong to the selected Contract."))  
<br/>contract = frappe.get_doc("Contract", doc.contract)  
<br/>if cert.certificate_type == "Final Acceptance":  
contract.db_set("final_acceptance_certificate", cert.name, update_modified=True)  
<br/><br/>def create_retention_ledger_entry_from_invoice(doc, method=None):  
if not doc.contract:  
return  
<br/>contract = frappe.get_doc("Contract", doc.contract)  
retention_pct = float(contract.retention_percentage or 0)  
<br/>if retention_pct <= 0:  
return  
<br/>retained_amount = (doc.grand_total or 0) \* retention_pct / 100.0  
if retained_amount <= 0:  
return  
<br/>balance = get_contract_retention_balance(contract.name) + retained_amount  
<br/>ledger = frappe.get_doc({  
"doctype": "Retention Ledger",  
"contract": contract.name,  
"purchase_invoice": doc.name,  
"retention_type": "Deduction",  
"posting_date": doc.posting_date or nowdate(),  
"amount": retained_amount,  
"balance_after_transaction": balance,  
"status": "Held",  
"remarks": f"Retention deducted from Purchase Invoice {doc.name}",  
})  
ledger.insert(ignore_permissions=True)  
<br/><br/>def get_contract_retention_balance(contract_name: str) -> float:  
rows = frappe.get_all(  
"Retention Ledger",  
filters={"contract": contract_name},  
fields=\["retention_type", "amount"\]  
)  
balance = 0.0  
for row in rows:  
if row.retention_type in ("Deduction",):  
balance += float(row.amount or 0)  
elif row.retention_type in ("Release", "Adjustment"):  
balance -= float(row.amount or 0)  
return balance  
<br/><br/>@frappe.whitelist()  
def release_retention(contract_name: str, amount: float, release_date: str | None = None):  
contract = frappe.get_doc("Contract", contract_name)  
balance = get_contract_retention_balance(contract.name)  
<br/>amount = float(amount)  
if amount <= 0:  
frappe.throw(\_("Release amount must be greater than zero."))  
if amount > balance:  
frappe.throw(\_("Release amount exceeds retained balance."))  
<br/>new_balance = balance - amount  
<br/>ledger = frappe.get_doc({  
"doctype": "Retention Ledger",  
"contract": contract.name,  
"retention_type": "Release",  
"posting_date": release_date or nowdate(),  
"amount": amount,  
"balance_after_transaction": new_balance,  
"release_date": release_date or nowdate(),  
"status": "Released",  
"remarks": "Manual retention release",  
})  
ledger.insert(ignore_permissions=True)  
<br/>return ledger.name

**hooks.py updates**

doc_events = {  
"Purchase Invoice": {  
"validate": "kentender.finance_integration.validate_purchase_invoice_certificate",  
"on_submit": "kentender.finance_integration.create_retention_ledger_entry_from_invoice",  
}  
}

Add these if not already present:

scheduler_events = {  
"daily": \[  
"kentender.contract_jobs.monitor_contract_expiry",  
"kentender.contract_jobs.monitor_dlp_expiry",  
\]  
}

**contract_jobs.py**

import frappe  
from frappe.utils import nowdate  
<br/><br/>def monitor_contract_expiry():  
contracts = frappe.get_all(  
"Contract",  
filters={"status": \["in", \["Active", "Suspended"\]\]},  
fields=\["name", "end_date"\]  
)  
<br/>today = nowdate()  
for c in contracts:  
if c.end_date and c.end_date < today:  
frappe.db.set_value("Contract", c.name, "status", "Closed")  
<br/><br/>def monitor_dlp_expiry():  
if not frappe.db.has_column("Contract", "dlp_end_date"):  
return  
<br/>contracts = frappe.get_all(  
"Contract",  
filters={"status": "Closed"},  
fields=\["name", "dlp_end_date"\]  
)  
<br/>today = nowdate()  
for c in contracts:  
if c.dlp_end_date and c.dlp_end_date < today:  
frappe.get_doc("Contract", c.name).add_comment(  
"Comment",  
"Defect Liability Period expired."  
)

**Custom fields to add**

**Project**

\[  
{  
"dt": "Project",  
"fieldname": "contract",  
"fieldtype": "Link",  
"options": "Contract",  
"label": "Contract",  
"insert_after": "project_name"  
}  
\]

**Task**

\[  
{  
"dt": "Task",  
"fieldname": "contract",  
"fieldtype": "Link",  
"options": "Contract",  
"label": "Contract",  
"insert_after": "project"  
},  
{  
"dt": "Task",  
"fieldname": "is_contract_milestone",  
"fieldtype": "Check",  
"label": "Is Contract Milestone",  
"insert_after": "contract"  
},  
{  
"dt": "Task",  
"fieldname": "payment_percentage",  
"fieldtype": "Percent",  
"label": "Payment Percentage",  
"insert_after": "is_contract_milestone"  
},  
{  
"dt": "Task",  
"fieldname": "acceptance_criteria",  
"fieldtype": "Small Text",  
"label": "Acceptance Criteria",  
"insert_after": "payment_percentage"  
},  
{  
"dt": "Task",  
"fieldname": "deliverables",  
"fieldtype": "Small Text",  
"label": "Deliverables",  
"insert_after": "acceptance_criteria"  
},  
{  
"dt": "Task",  
"fieldname": "supplier_confirmed",  
"fieldtype": "Check",  
"label": "Supplier Confirmed",  
"insert_after": "deliverables"  
},  
{  
"dt": "Task",  
"fieldname": "milestone_status",  
"fieldtype": "Select",  
"options": "Pending\\nCompleted\\nAccepted\\nRejected",  
"label": "Milestone Status",  
"insert_after": "supplier_confirmed"  
}  
\]

**Purchase Receipt**

\[  
{  
"dt": "Purchase Receipt",  
"fieldname": "contract",  
"fieldtype": "Link",  
"options": "Contract",  
"label": "Contract",  
"insert_after": "supplier"  
},  
{  
"dt": "Purchase Receipt",  
"fieldname": "milestone_task",  
"fieldtype": "Link",  
"options": "Task",  
"label": "Milestone Task",  
"insert_after": "contract"  
}  
\]

**Purchase Invoice**

\[  
{  
"dt": "Purchase Invoice",  
"fieldname": "contract",  
"fieldtype": "Link",  
"options": "Contract",  
"label": "Contract",  
"insert_after": "supplier"  
},  
{  
"dt": "Purchase Invoice",  
"fieldname": "acceptance_certificate",  
"fieldtype": "Link",  
"options": "Acceptance Certificate",  
"label": "Acceptance Certificate",  
"insert_after": "contract"  
},  
{  
"dt": "Purchase Invoice",  
"fieldname": "milestone_task",  
"fieldtype": "Link",  
"options": "Task",  
"label": "Milestone Task",  
"insert_after": "acceptance_certificate"  
}  
\]

**What this gives you immediately**

This package wires the most important CLM spine:

- **Tender award → Contract**
- **Contract activation → Project**
- **Contract execution → Task milestones**
- **Inspection readiness → Quality gate**
- **Certificate → invoice control**
- **Invoice → retention deduction**
- **Final acceptance → DLP entry point**

**What still needs the next pass**

This code is the right backbone, but these areas are still pending:

- variation implementation into PO and Task dates
- claims and disputes workflows
- certificate issuance workflow logic
- Purchase Receipt auto-linking for goods contracts
- CIT and Inspection Committee approval logic
- termination and close-out enforcement

The right next move is **C: full workflows**, because now the data model and integration spine are stable.

**CLM workflow architecture**

I would split this into **10 focused workflows**, not one giant monster workflow. That keeps permissions sane, makes auditing cleaner, and avoids blocking unrelated activities.

**1\. Contract workflow**

This is the master governance workflow.

**States**

- Draft
- Pending Internal Review
- Pending Supplier Signature
- Pending Accounting Officer Signature
- Active
- Suspended
- Pending Termination Approval
- Terminated
- Pending Close-Out
- Closed

**Transitions**

- Draft → Pending Internal Review  
    Triggered by Head of Procurement after contract prep is complete.
- Pending Internal Review → Pending Supplier Signature  
    Triggered by internal approval.
- Pending Supplier Signature → Pending Accounting Officer Signature  
    Triggered after supplier signs.
- Pending Accounting Officer Signature → Active  
    Triggered after Accounting Officer signs.
- Active → Suspended  
    Triggered by authorized decision, including dispute or stop-work conditions.
- Active → Pending Termination Approval  
    Triggered when termination is proposed.
- Pending Termination Approval → Terminated  
    Triggered only by Accounting Officer.
- Active → Pending Close-Out  
    Triggered once final acceptance exists and operational completion is reached.
- Pending Close-Out → Closed  
    Triggered once all payments are complete and handover is complete.

**Key guards**

- Contract cannot become Active before both signatures are complete.
- Contract cannot become Closed until final acceptance, payments, and handover are all complete.

**2\. Contract Implementation Team workflow**

This should be lightweight but formal.

**States**

- Proposed
- Under Approval
- Approved
- Active
- Removed

**Transitions**

- Proposed → Under Approval  
    Triggered by Head of Procurement recommendation.
- Under Approval → Approved  
    Triggered by Accounting Officer.
- Approved → Active  
    Triggered when contract becomes Active.
- Active → Removed  
    Triggered by replacement/removal decision.

**Notes**

- This is not a contract workflow substitute.
- It controls who is authorized to verify milestones and implementation activity.

**3\. Inspection Committee workflow**

Separate from CIT, because your FRS distinguishes them.

**States**

- Proposed
- Under Approval
- Approved
- Active
- Dissolved

**Transitions**

- Proposed → Under Approval  
    By Head of Procurement
- Under Approval → Approved  
    By Accounting Officer or delegated approver
- Approved → Active  
    When first inspection is initiated
- Active → Dissolved  
    At close-out or replacement

**4\. Milestone execution workflow**

Use ERPNext Task as the milestone object, with custom milestone fields.

**States**

- Pending
- In Progress
- Completed by Supplier
- Verified by CIT
- Sent for Inspection
- Accepted
- Rejected
- Payment Eligible

**Transitions**

- Pending → In Progress  
    When execution begins
- In Progress → Completed by Supplier  
    Supplier confirms completion/delivery
- Completed by Supplier → Verified by CIT  
    CIT records completion minutes and verification
- Verified by CIT → Sent for Inspection  
    Head of Procurement or system pushes it forward
- Sent for Inspection → Accepted  
    Inspection and acceptance passes
- Sent for Inspection → Rejected  
    Failed inspection/testing
- Accepted → Payment Eligible  
    Once correct certificate is issued

**Notes**

- Goods, works, and services can share this workflow, but activity logs differ by contract type.
- For goods, Purchase Receipt should be linked before or during inspection where applicable.

**5\. Acceptance Certificate workflow**

You already chose one DocType with certificate_type, which is correct.

**States**

- Draft
- Under Review
- Approved
- Rejected
- Issued
- Cancelled

**Transitions**

- Draft → Under Review  
    Created after milestone/inspection evidence exists
- Under Review → Approved  
    By the correct authority depending on certificate type
- Under Review → Rejected  
    If evidence is insufficient
- Approved → Issued  
    System stamps and locks certificate
- Issued → Cancelled  
    Exceptional case only, with audit reason

**Approval authority by certificate type**

- Interim Acceptance → based on milestone completion and inspection outcome
- Certificate of Conformance → Head of User Department
- Certificate of Acceptance → Head of Procurement
- Final Acceptance → Accounting Officer

**Key guard**

- Purchase Invoice cannot proceed without a valid issued certificate.

**6\. Purchase Invoice / payment approval workflow**

The accounting documents remain ERPNext-native, but the workflow must enforce your CLM rules.

**Purchase Invoice states**

- Draft
- Submitted by Supplier
- Under Procurement Review
- Pending Finance Verification
- Pending Procurement Certification
- Approved for Payment
- Paid
- Partially Paid
- Rejected

**Transitions**

- Draft → Submitted by Supplier  
    Supplier submits invoice
- Submitted by Supplier → Under Procurement Review  
    System/Head of Procurement
- Under Procurement Review → Pending Finance Verification  
    Head of Procurement forwards
- Pending Finance Verification → Pending Procurement Certification  
    Head of Finance verifies
- Pending Procurement Certification → Approved for Payment  
    Head of Procurement certifies voucher
- Approved for Payment → Paid / Partially Paid  
    Finance processes payment and posts to GL
- Any review state → Rejected  
    If invoice is invalid

**Key guards**

- Invoice must reference Contract, Milestone Task, and Acceptance Certificate.
- Final payment requires Final Acceptance Certificate.
- Statutory deductions and retention must be computed before payment finalization.

**7\. Retention workflow**

Retention should not be a passive ledger only. It needs a control workflow.

**States**

- Held
- Partially Released
- Eligible for Release
- Released
- Adjusted
- Forfeited

**Transitions**

- Held → Partially Released  
    Partial release event
- Held → Eligible for Release  
    Retention period ends or contractual condition met
- Eligible for Release → Released  
    Approved release
- Held / Eligible for Release → Adjusted  
    Deduction applied against retention
- Held / Eligible for Release → Forfeited  
    Where contractually justified

**Key guards**

- Funds remain locked until retention period ends unless deductions are applied.

**8\. Contract Variation workflow**

This one must be strict because it can affect value, time, and scope.

**States**

- Draft
- Submitted
- Under Technical Review
- Under Financial Review
- Pending Approval
- Approved
- Rejected
- Implemented

**Transitions**

- Draft → Submitted  
    Raised by authorized user
- Submitted → Under Technical Review  
    For scope/time analysis
- Under Technical Review → Under Financial Review  
    If technically viable
- Under Financial Review → Pending Approval  
    Once cost impact is assessed
- Pending Approval → Approved  
    By designated authority
- Pending Approval → Rejected  
    If unjustified
- Approved → Implemented  
    After updates propagate to Contract / Project / Task / PO

**Key rule**

Every variation must have justification, approval workflow, and financial impact.

**9\. Claim and dispute workflows**

These should be separate but linked.

**Claim states**

- Draft
- Submitted
- Under Review
- Recommended
- Approved
- Rejected
- Settled
- Escalated to Dispute

**Claim transitions**

- Draft → Submitted
- Submitted → Under Review
- Under Review → Recommended
- Recommended → Approved / Rejected
- Approved → Settled
- Any review state → Escalated to Dispute

**Dispute states**

- Notice of Claim
- Negotiation
- Mediation
- Arbitration
- Resolved
- Closed

**Dispute transitions**

- Notice of Claim → Negotiation
- Negotiation → Mediation
- Mediation → Arbitration
- Any stage → Resolved
- Resolved → Closed

**Notes**

- Stop Work Order should be a controlled action available during dispute handling, triggered by Accounting Officer based on advice from CIT and Head of Procurement.

**10\. Termination, close-out, and DLP workflows**

These should be distinct, not merged.

**Termination Record states**

- Draft
- Under Legal Review
- Pending Accounting Officer Approval
- Approved
- Executed
- Cancelled

**Transitions**

- Draft → Under Legal Review
- Under Legal Review → Pending Accounting Officer Approval
- Pending Accounting Officer Approval → Approved
- Approved → Executed
- Any pre-execution state → Cancelled

**Key rule**

Termination requires Accounting Officer approval and documented justification.

**Close-out states**

- Not Ready
- Ready for Close-Out
- Under Final Review
- Archived

**Transitions**

- Not Ready → Ready for Close-Out  
    When final acceptance, payments, and handover are complete
- Ready for Close-Out → Under Final Review
- Under Final Review → Archived

**DLP states**

- Not Started
- Active
- Defect Reported
- Under Remedy
- Completed
- Reopened

**Transitions**

- Not Started → Active  
    Starts after handover / close-out transition
- Active → Defect Reported  
    On defect notification
- Defect Reported → Under Remedy
- Under Remedy → Active  
    If remedied and DLP continues
- Active → Completed  
    At DLP expiry
- Completed → Reopened  
    Only if rules allow contract reopening due to defect

**Role matrix for workflow authority**

**Head of Procurement**

Owns:

- contract preparation
- contract monitoring
- CIT recommendation
- inspection committee recommendation
- certificate of acceptance
- procurement review of invoices
- voucher certification
- variation initiation/review

**Accounting Officer**

Owns:

- final contract signature
- CIT appointment
- final acceptance certificate
- stop work authorization
- termination approval

**CIT**

Owns:

- implementation supervision
- milestone verification
- implementation minutes
- technical progress evidence

**Inspection and Acceptance Committee**

Owns:

- inspection execution
- testing evidence
- inspection decision

**Head of User Department**

Owns:

- certificate of conformance

**Head of Finance**

Owns:

- invoice verification
- payment processing validation

**Supplier**

Owns:

- contract signature
- milestone completion confirmation
- invoice submission
- contractor claims

**ERPNext workflow boundaries**

To keep this clean, I would apply workflows like this:

**Custom DocTypes with Frappe workflows**

- Contract
- Acceptance Certificate
- Contract Variation
- Claim
- Dispute Case
- Termination Record
- Defect Liability Case
- CIT Member
- Inspection Committee Member

**ERPNext DocTypes with either workflow or server-side guards**

- Purchase Invoice
- Payment Entry
- Task
- Purchase Receipt
- Quality Inspection

I would not over-customize native ERPNext flows where a server-side validation is enough.

**Non-negotiable workflow guards**

These need to be enforced in code, not just visually in workflows:

- Contract cannot activate before both signatures.
- Payment cannot proceed without valid certificate.
- Final payment cannot proceed without Final Acceptance Certificate.
- Retention cannot release early unless an allowed adjustment path exists.
- Termination cannot execute without Accounting Officer approval.

**My recommendation on implementation order**

Do these workflows in this sequence:

1.  Contract
2.  Acceptance Certificate
3.  Purchase Invoice / payment control
4.  Milestone Task workflow
5.  Variation
6.  Claim / Dispute
7.  Termination
8.  Retention
9.  Close-out / DLP
10. CIT / Inspection committee assignment

That order matches operational risk. It gets the core legal-financial controls live first.

The right next move is to generate the **actual workflow definitions** for the first three:

- Contract
- Acceptance Certificate
- Purchase Invoice control

That is the highest-value slice.

**🧾 1. CONTRACT WORKFLOW (CORE GOVERNANCE)**

**Workflow: Contract Workflow**

{  
"workflow_name": "Contract Workflow",  
"document_type": "Contract",  
"is_active": 1,  
"workflow_state_field": "status",  
"states": \[  
{"state": "Draft", "doc_status": 0},  
{"state": "Pending Internal Review", "doc_status": 0},  
{"state": "Pending Supplier Signature", "doc_status": 0},  
{"state": "Pending Accounting Officer Signature", "doc_status": 0},  
{"state": "Active", "doc_status": 0},  
{"state": "Suspended", "doc_status": 0},  
{"state": "Pending Termination Approval", "doc_status": 0},  
{"state": "Terminated", "doc_status": 0},  
{"state": "Pending Close-Out", "doc_status": 0},  
{"state": "Closed", "doc_status": 0}  
\]  
}

**Transitions**

\[  
{  
"state": "Draft",  
"action": "Submit for Review",  
"next_state": "Pending Internal Review",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Pending Internal Review",  
"action": "Approve Internal",  
"next_state": "Pending Supplier Signature",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Pending Supplier Signature",  
"action": "Supplier Signs",  
"next_state": "Pending Accounting Officer Signature",  
"allowed": "Supplier"  
},  
{  
"state": "Pending Accounting Officer Signature",  
"action": "Approve & Activate",  
"next_state": "Active",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Active",  
"action": "Suspend",  
"next_state": "Suspended",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Active",  
"action": "Request Termination",  
"next_state": "Pending Termination Approval",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Pending Termination Approval",  
"action": "Approve Termination",  
"next_state": "Terminated",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Active",  
"action": "Ready for Close-Out",  
"next_state": "Pending Close-Out",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Pending Close-Out",  
"action": "Close Contract",  
"next_state": "Closed",  
"allowed": "Accounting Officer"  
}  
\]

**🔒 Critical Server Guards (DO NOT SKIP)**

def validate_contract_activation(doc):  
if doc.status == "Active":  
if not (doc.signed_by_supplier and doc.signed_by_accounting_officer):  
frappe.throw("Contract cannot activate without both signatures.")

def validate_contract_closure(doc):  
if doc.status == "Closed":  
if not doc.final_acceptance_certificate:  
frappe.throw("Final Acceptance Certificate required before closing.")

**📜 2. ACCEPTANCE CERTIFICATE WORKFLOW**

**Workflow: Acceptance Certificate Workflow**

{  
"workflow_name": "Acceptance Certificate Workflow",  
"document_type": "Acceptance Certificate",  
"workflow_state_field": "workflow_state",  
"is_active": 1,  
"states": \[  
{"state": "Draft"},  
{"state": "Under Review"},  
{"state": "Approved"},  
{"state": "Rejected"},  
{"state": "Issued"},  
{"state": "Cancelled"}  
\]  
}

**Transitions**

\[  
{  
"state": "Draft",  
"action": "Submit",  
"next_state": "Under Review",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Under Review",  
"action": "Approve",  
"next_state": "Approved",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Under Review",  
"action": "Reject",  
"next_state": "Rejected",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Approved",  
"action": "Issue Certificate",  
"next_state": "Issued",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Issued",  
"action": "Cancel",  
"next_state": "Cancelled",  
"allowed": "Accounting Officer"  
}  
\]

**🔒 Authority Logic (CRITICAL — dynamic)**

def validate_certificate_approval(doc):  
if doc.workflow_state == "Approved":  
if doc.certificate_type == "Final Acceptance":  
if not user_has_role("Accounting Officer"):  
frappe.throw("Final Acceptance requires Accounting Officer approval.")  
<br/>elif doc.certificate_type == "Certificate of Conformance":  
if not user_has_role("Head of User Department"):  
frappe.throw("Conformance certificate requires User Department approval.")

**🔗 Integration Rule**

def on_certificate_issued(doc):  
if doc.certificate_type == "Final Acceptance":  
frappe.db.set_value("Contract", doc.contract, "final_acceptance_certificate", doc.name)

**💰 3. PURCHASE INVOICE CONTROL WORKFLOW**

We DO NOT override ERPNext fully.  
We **layer controls on top**.

**Workflow: CLM Purchase Invoice Workflow**

{  
"workflow_name": "CLM Purchase Invoice Workflow",  
"document_type": "Purchase Invoice",  
"workflow_state_field": "approval_status",  
"is_active": 1,  
"states": \[  
{"state": "Draft"},  
{"state": "Submitted by Supplier"},  
{"state": "Under Procurement Review"},  
{"state": "Pending Finance Verification"},  
{"state": "Pending Procurement Certification"},  
{"state": "Approved for Payment"},  
{"state": "Rejected"}  
\]  
}

**Transitions**

\[  
{  
"state": "Draft",  
"action": "Submit Invoice",  
"next_state": "Submitted by Supplier",  
"allowed": "Supplier"  
},  
{  
"state": "Submitted by Supplier",  
"action": "Review",  
"next_state": "Under Procurement Review",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Under Procurement Review",  
"action": "Forward to Finance",  
"next_state": "Pending Finance Verification",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Pending Finance Verification",  
"action": "Verify",  
"next_state": "Pending Procurement Certification",  
"allowed": "Head of Finance"  
},  
{  
"state": "Pending Procurement Certification",  
"action": "Certify",  
"next_state": "Approved for Payment",  
"allowed": "Head of Procurement"  
},  
{  
"state": "\*",  
"action": "Reject",  
"next_state": "Rejected",  
"allowed": "Head of Procurement"  
}  
\]

**🔒 Hard Enforcement (THIS IS NON-NEGOTIABLE)**

def validate_invoice_requirements(doc):  
if doc.contract:  
if not doc.acceptance_certificate:  
frappe.throw("Invoice requires Acceptance Certificate.")  
<br/>cert = frappe.get_doc("Acceptance Certificate", doc.acceptance_certificate)  
<br/>if cert.workflow_state != "Issued":  
frappe.throw("Certificate must be issued.")  
<br/>if cert.certificate_type == "Final Acceptance":  
\# OK for final payment  
return

**🔗 Retention Hook (already built, now enforced)**

def before_payment(doc):  
if doc.approval_status != "Approved for Payment":  
frappe.throw("Invoice must be fully approved before payment.")

**🧠 WHAT YOU NOW HAVE**

You now have:

**Governance Layer**

- Contract workflow (legal + lifecycle)

**Control Layer**

- Certificate workflow (technical + acceptance)

**Financial Gatekeeping**

- Invoice workflow (payment control)

**⚠️ What you just did (this matters)**

You’ve enforced:

- No contract activation without signatures
- No invoice without acceptance
- No payment without certification
- No close-out without final acceptance

👉 This is **public procurement-grade control**

**🚀 NEXT STEP (HIGH IMPACT)**

Now we move to:

**👉 Milestone + Task + Quality workflow integration**

This is where:

- execution meets validation
- and most systems fall apart if done poorly

Milestone workflows are where your CLM either becomes operationally strong or turns into a paperwork machine. Since you want tight ERPNext integration, the milestone engine should be built on **Project + Task + Quality Inspection + Purchase Receipt**, with only the governance pieces staying custom. That fits your requirements for milestone monitoring, implementation activities, inspection/testing, certification, and invoice gating.

**Milestone workflow design**

**Core modeling decision**

A “milestone” should be an ERPNext **Task** with contract-specific custom fields, not a separate custom DocType. That gives you timeline control, ownership, progress tracking, and Project integration without duplication.

**Task custom fields used as milestone controls**

You already approved this direction. The milestone-relevant fields should include:

- contract
- is_contract_milestone
- payment_percentage
- acceptance_criteria
- deliverables
- supplier_confirmed
- milestone_status

I would also add these two fields because they are operationally necessary:

\[  
{  
"dt": "Task",  
"fieldname": "contract_type",  
"fieldtype": "Select",  
"options": "Goods\\nWorks\\nServices",  
"label": "Contract Type",  
"insert_after": "milestone_status"  
},  
{  
"dt": "Task",  
"fieldname": "quality_inspection_required",  
"fieldtype": "Check",  
"label": "Quality Inspection Required",  
"insert_after": "contract_type"  
}  
\]

Those let the workflow adapt cleanly by contract type and by whether inspection is mandatory.

**1\. Milestone workflow states**

Use milestone_status on Task as the workflow field.

**Workflow: Contract Milestone Workflow**

**States**

- Pending
- In Progress
- Completed by Supplier
- Verified by CIT
- Sent for Inspection
- Accepted
- Rejected
- Payment Eligible

These states are directly aligned with your requirements:

- supplier completion confirmation
- CIT verification
- inspection/testing
- acceptance decision
- certificate-driven payment eligibility

**2\. Milestone workflow definition**

{  
"workflow_name": "Contract Milestone Workflow",  
"document_type": "Task",  
"is_active": 1,  
"workflow_state_field": "milestone_status",  
"states": \[  
{"state": "Pending", "doc_status": 0},  
{"state": "In Progress", "doc_status": 0},  
{"state": "Completed by Supplier", "doc_status": 0},  
{"state": "Verified by CIT", "doc_status": 0},  
{"state": "Sent for Inspection", "doc_status": 0},  
{"state": "Accepted", "doc_status": 0},  
{"state": "Rejected", "doc_status": 0},  
{"state": "Payment Eligible", "doc_status": 0}  
\]  
}

**3\. Milestone workflow transitions**

\[  
{  
"state": "Pending",  
"action": "Start Work",  
"next_state": "In Progress",  
"allowed": "Contract Implementation Team"  
},  
{  
"state": "In Progress",  
"action": "Confirm Completion",  
"next_state": "Completed by Supplier",  
"allowed": "Supplier"  
},  
{  
"state": "Completed by Supplier",  
"action": "Verify by CIT",  
"next_state": "Verified by CIT",  
"allowed": "Contract Implementation Team"  
},  
{  
"state": "Verified by CIT",  
"action": "Send for Inspection",  
"next_state": "Sent for Inspection",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Sent for Inspection",  
"action": "Accept Milestone",  
"next_state": "Accepted",  
"allowed": "Inspection and Acceptance Committee"  
},  
{  
"state": "Sent for Inspection",  
"action": "Reject Milestone",  
"next_state": "Rejected",  
"allowed": "Inspection and Acceptance Committee"  
},  
{  
"state": "Accepted",  
"action": "Mark Payment Eligible",  
"next_state": "Payment Eligible",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Rejected",  
"action": "Reopen Milestone",  
"next_state": "In Progress",  
"allowed": "Head of Procurement"  
}  
\]

**4\. Contract-type behavior**

This workflow should behave slightly differently depending on contract type.

**Goods contracts**

Expected sequence:

- Completed by Supplier
- Purchase Receipt recorded
- Quality Inspection run
- Accepted / Rejected
- Certificate
- Payment Eligible

This maps to your goods delivery and GRN requirement.

**Works contracts**

Expected sequence:

- Completed by Supplier
- CIT verifies site progress and completion minutes
- Quality/inspection may still apply where needed
- Accepted / Rejected
- Certificate
- Payment Eligible

This maps to site handover, site meetings, milestone verification, and technical acceptance.

**Services contracts**

Expected sequence:

- Completed by Supplier
- CIT verifies service delivery
- Inspection optional depending on service type
- Acceptance / certificate
- Payment Eligible

**5\. Non-negotiable server-side guards**

Do not rely on the visual workflow alone. These conditions must be enforced in code.

**A. Only milestone Tasks should use this workflow**

def validate_contract_milestone_task(doc):  
if doc.milestone_status and not doc.is_contract_milestone:  
frappe.throw("Only contract milestone tasks can use milestone workflow states.")

**B. Supplier completion requires supplier confirmation**

def validate_supplier_completion(doc):  
if doc.milestone_status == "Completed by Supplier" and not doc.supplier_confirmed:  
frappe.throw("Supplier confirmation is required before milestone completion.")

**C. CIT verification requires active contract**

def validate_cit_verification(doc):  
if doc.milestone_status == "Verified by CIT":  
contract = frappe.get_doc("Contract", doc.contract)  
if contract.status != "Active":  
frappe.throw("Milestone verification is only allowed for active contracts.")

**D. Inspection state requires Quality Inspection when required**

def validate_inspection_gate(doc):  
if doc.milestone_status in ("Accepted", "Rejected", "Payment Eligible"):  
if doc.quality_inspection_required:  
qi = frappe.db.get_value(  
"Quality Inspection",  
{"reference_type": "Task", "reference_name": doc.name},  
"name"  
)  
if not qi:  
frappe.throw("Quality Inspection is required before milestone acceptance.")

**E. Payment Eligible requires issued certificate**

def validate_payment_eligibility(doc):  
if doc.milestone_status == "Payment Eligible":  
cert = frappe.db.get_value(  
"Acceptance Certificate",  
{  
"task": doc.name,  
"workflow_state": "Issued",  
"decision": "Approved"  
},  
"name"  
)  
if not cert:  
frappe.throw("An issued approved Acceptance Certificate is required before payment eligibility.")

These guards directly support your rules on inspection, certification, and payment control.

**6\. Purchase Receipt integration for goods milestones**

For goods contracts, milestone acceptance should be tied to ERPNext receiving.

**Required rule**

If contract_type == "Goods", then before acceptance:

- there must be a linked Purchase Receipt
- that receipt should reference the same contract and milestone task

**Custom fields already identified on Purchase Receipt**

- contract
- milestone_task

**Guard**

def validate_goods_receipt_before_acceptance(doc):  
if doc.contract_type == "Goods" and doc.milestone_status in ("Accepted", "Payment Eligible"):  
pr = frappe.db.get_value(  
"Purchase Receipt",  
{"contract": doc.contract, "milestone_task": doc.name},  
"name"  
)  
if not pr:  
frappe.throw("Goods milestones require a linked Purchase Receipt before acceptance.")

That directly covers your GRN requirement using ERPNext-native receiving instead of a duplicate custom object.

**7\. Quality Inspection integration**

Since you want tight ERPNext integration, inspection/testing should use ERPNext Quality rather than a custom inspection engine.

**Rule**

A milestone in Sent for Inspection should:

- create or link a Quality Inspection
- enforce accepted result before milestone acceptance

**Suggested automation**

def on_send_for_inspection(doc):  
if doc.quality_inspection_required:  
existing = frappe.db.get_value(  
"Quality Inspection",  
{"reference_type": "Task", "reference_name": doc.name},  
"name"  
)  
if not existing:  
from kentender.quality_integration import create_quality_inspection_for_task  
create_quality_inspection_for_task(doc.name)

**Accepted result guard**

def validate_quality_result_for_acceptance(doc):  
if doc.milestone_status == "Accepted" and doc.quality_inspection_required:  
qi_name = frappe.db.get_value(  
"Quality Inspection",  
{"reference_type": "Task", "reference_name": doc.name},  
"name"  
)  
if not qi_name:  
frappe.throw("Quality Inspection is missing.")  
<br/>qi = frappe.get_doc("Quality Inspection", qi_name)  
accepted = getattr(qi, "status", None) in ("Accepted", "Completed") or getattr(qi, "report_status", None) == "Accepted"  
if not accepted:  
frappe.throw("Quality Inspection must be accepted before milestone acceptance.")

**8\. Certificate integration**

Milestone workflow should not directly create invoices. It should only unlock certificate issuance and then payment eligibility.

**Recommended sequence**

- Accepted milestone
- corresponding certificate created and issued
- milestone becomes Payment Eligible

**Automation option**

When milestone is accepted, auto-create a draft Acceptance Certificate:

def create_draft_certificate_for_accepted_milestone(doc):  
if doc.milestone_status != "Accepted":  
return  
<br/>existing = frappe.db.get_value(  
"Acceptance Certificate",  
{"task": doc.name, "workflow_state": \["!=", "Cancelled"\]},  
"name"  
)  
if existing:  
return  
<br/>cert = frappe.get_doc({  
"doctype": "Acceptance Certificate",  
"certificate_type": "Interim Acceptance",  
"contract": doc.contract,  
"project": doc.project,  
"task": doc.name,  
"issued_by": frappe.session.user,  
"issued_on": frappe.utils.now_datetime(),  
"decision": "Approved",  
"workflow_state": "Draft"  
})  
cert.insert(ignore_permissions=True)

For final milestone acceptance, the certificate type can be determined by business rules:

- final milestone → possibly Final Acceptance
- non-technical delivery → Certificate of Acceptance
- technically complex delivery → Certificate of Conformance or Final Acceptance

**9\. Comments, minutes, and audit evidence**

Your FRS explicitly requires milestone completion minutes and implementation activity logging.

Do not bury that in random comments only.

**Recommended lightweight addition**

Add a custom DocType:

- Contract Activity Log

Use it for:

- site handover
- site meetings
- milestone verification minutes
- delivery confirmations
- implementation notes

**Minimal structure**

- contract
- project
- task
- activity_type
- activity_date
- recorded_by
- summary

That is much better than overloading Task comments for formal evidence.

**10\. Suggested hooks**

**hooks.py**

doc_events = {  
"Task": {  
"validate": "kentender.milestone_workflow.validate_task_milestone_rules",  
"on_update": "kentender.milestone_workflow.handle_task_milestone_events"  
}  
}

**milestone_workflow.py**

def validate_task_milestone_rules(doc, method=None):  
if not doc.is_contract_milestone:  
return  
<br/>validate_contract_milestone_task(doc)  
validate_supplier_completion(doc)  
validate_cit_verification(doc)  
validate_inspection_gate(doc)  
validate_goods_receipt_before_acceptance(doc)  
validate_quality_result_for_acceptance(doc)  
validate_payment_eligibility(doc)  
<br/><br/>def handle_task_milestone_events(doc, method=None):  
if not doc.is_contract_milestone:  
return  
<br/>if doc.milestone_status == "Sent for Inspection":  
on_send_for_inspection(doc)  
<br/>if doc.milestone_status == "Accepted":  
create_draft_certificate_for_accepted_milestone(doc)

**11\. What this milestone layer now enforces**

You now have an execution workflow that properly ties together:

- **Task** as milestone
- **Purchase Receipt** for goods receiving
- **Quality Inspection** for testing/inspection
- **Acceptance Certificate** for formal acceptance
- **Purchase Invoice** eligibility only after approval chain

That is exactly the right ERPNext-aligned structure for your requirements.

Good. These three belong together.

Why? Because in your CLM requirements, **variations** change the contract during execution, **close-out** ends the active execution phase, and **DLP** governs the post-handover liability phase. If you model them separately without tight rules, you get broken timelines, wrong financial positions, and contracts that “close” while still legally exposed. Your requirements explicitly call for support for contract amendments, contract close-out, and defect liability management.

**1\. Contract Variation workflow**

This workflow must be strict because it can affect:

- scope
- time
- cost
- downstream ERPNext records such as Project, Task dates, and Purchase Order values

Your requirements say each variation must include **justification, approval workflow, and financial impact**.

**States**

- Draft
- Submitted
- Under Technical Review
- Under Financial Review
- Pending Approval
- Approved
- Rejected
- Implemented

**Workflow definition**

{  
"workflow_name": "Contract Variation Workflow",  
"document_type": "Contract Variation",  
"is_active": 1,  
"workflow_state_field": "status",  
"states": \[  
{"state": "Draft", "doc_status": 0},  
{"state": "Submitted", "doc_status": 0},  
{"state": "Under Technical Review", "doc_status": 0},  
{"state": "Under Financial Review", "doc_status": 0},  
{"state": "Pending Approval", "doc_status": 0},  
{"state": "Approved", "doc_status": 0},  
{"state": "Rejected", "doc_status": 0},  
{"state": "Implemented", "doc_status": 0}  
\]  
}

**Transitions**

\[  
{  
"state": "Draft",  
"action": "Submit Variation",  
"next_state": "Submitted",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Submitted",  
"action": "Start Technical Review",  
"next_state": "Under Technical Review",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Under Technical Review",  
"action": "Forward to Finance",  
"next_state": "Under Financial Review",  
"allowed": "Contract Implementation Team"  
},  
{  
"state": "Under Financial Review",  
"action": "Forward for Approval",  
"next_state": "Pending Approval",  
"allowed": "Head of Finance"  
},  
{  
"state": "Pending Approval",  
"action": "Approve Variation",  
"next_state": "Approved",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Pending Approval",  
"action": "Reject Variation",  
"next_state": "Rejected",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Approved",  
"action": "Implement Variation",  
"next_state": "Implemented",  
"allowed": "Head of Procurement"  
}  
\]

**Required guards**

**A. Variation must be tied to an active contract**

def validate_variation_contract_state(doc):  
contract = frappe.get_doc("Contract", doc.contract)  
if contract.status != "Active":  
frappe.throw("Variations are only allowed on active contracts.")

**B. Variation must have justification**

def validate_variation_justification(doc):  
if doc.status in ("Submitted", "Under Technical Review", "Under Financial Review", "Pending Approval", "Approved", "Implemented"):  
if not doc.justification:  
frappe.throw("Variation justification is required.")

**C. Type-specific rules**

def validate_variation_type_requirements(doc):  
if doc.variation_type == "Cost Adjustment" and not doc.financial_impact:  
frappe.throw("Cost Adjustment variation requires financial impact.")  
<br/>if doc.variation_type == "Time Extension" and not doc.time_extension_days:  
frappe.throw("Time Extension variation requires extension days.")

**Implementation hook**

When status changes to Implemented, push changes into ERPNext-linked records:

- Contract.revised_contract_value or equivalent computed update
- Project.expected_end_date
- milestone Task.exp_end_date
- Purchase Order amount if policy allows PO amendment

def implement_variation_effects(doc):  
if doc.status != "Implemented":  
return  
<br/>contract = frappe.get_doc("Contract", doc.contract)  
<br/>if doc.revised_contract_value:  
contract.contract_value = doc.revised_contract_value  
<br/>if doc.revised_end_date:  
contract.end_date = doc.revised_end_date  
<br/>contract.save(ignore_permissions=True)  
<br/>if contract.project and doc.revised_end_date:  
frappe.db.set_value("Project", contract.project, "expected_end_date", doc.revised_end_date)  
<br/>tasks = frappe.get_all(  
"Task",  
filters={"contract": contract.name, "is_contract_milestone": 1},  
fields=\["name", "exp_end_date"\]  
)  
for t in tasks:  
\# Replace with smarter rescheduling logic later  
frappe.db.set_value("Task", t.name, "exp_end_date", doc.revised_end_date)

That directly supports scope/time/cost change control from your requirements.

**2\. Contract close-out workflow**

Your requirements say close-out occurs when:

- Final Acceptance Certificate issued
- All payments completed
- Goods or works handed over
- Contract record archived

This should not be mixed into the master Contract workflow as a loose final click. It needs explicit readiness checks.

**States**

Use Contract status for the high-level transition:

- Active
- Pending Close-Out
- Closed

But add a dedicated close_out_status field on Contract for operational clarity:

- Not Ready
- Ready for Close-Out
- Under Final Review
- Archived

**Suggested custom field on Contract**

\[  
{  
"dt": "Contract",  
"fieldname": "close_out_status",  
"fieldtype": "Select",  
"options": "Not Ready\\nReady for Close-Out\\nUnder Final Review\\nArchived",  
"label": "Close-Out Status",  
"insert_after": "status"  
},  
{  
"dt": "Contract",  
"fieldname": "handover_completed",  
"fieldtype": "Check",  
"label": "Handover Completed",  
"insert_after": "close_out_status"  
},  
{  
"dt": "Contract",  
"fieldname": "all_payments_completed",  
"fieldtype": "Check",  
"label": "All Payments Completed",  
"insert_after": "handover_completed"  
},  
{  
"dt": "Contract",  
"fieldname": "close_out_date",  
"fieldtype": "Date",  
"label": "Close-Out Date",  
"insert_after": "all_payments_completed"  
}  
\]

**Close-out transitions**

\[  
{  
"state": "Not Ready",  
"action": "Mark Ready for Close-Out",  
"next_state": "Ready for Close-Out",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Ready for Close-Out",  
"action": "Start Final Review",  
"next_state": "Under Final Review",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Under Final Review",  
"action": "Archive Contract",  
"next_state": "Archived",  
"allowed": "Accounting Officer"  
}  
\]

**Required close-out guards**

**A. Final Acceptance Certificate must exist and be issued**

def validate_close_out_final_acceptance(contract):  
if contract.close_out_status in ("Ready for Close-Out", "Under Final Review", "Archived"):  
if not contract.final_acceptance_certificate:  
frappe.throw("Final Acceptance Certificate is required for close-out.")  
<br/>cert = frappe.get_doc("Acceptance Certificate", contract.final_acceptance_certificate)  
if cert.workflow_state != "Issued" or cert.decision != "Approved":  
frappe.throw("Final Acceptance Certificate must be issued and approved.")

**B. All payments must be complete**

def validate_close_out_payments(contract):  
if contract.close_out_status in ("Ready for Close-Out", "Under Final Review", "Archived"):  
unpaid = frappe.db.sql("""  
select name  
from \`tabPurchase Invoice\`  
where contract = %s  
and docstatus = 1  
and outstanding_amount > 0  
limit 1  
""", contract.name)  
<br/>if unpaid:  
frappe.throw("All contract invoices must be fully paid before close-out.")

**C. Handover must be complete**

def validate_close_out_handover(contract):  
if contract.close_out_status in ("Ready for Close-Out", "Under Final Review", "Archived"):  
if not contract.handover_completed:  
frappe.throw("Handover must be completed before close-out.")

**Close-out action**

When close_out_status = Archived:

- set Contract.status = Closed
- set close_out_date
- start DLP if applicable

def finalize_contract_close_out(contract):  
if contract.close_out_status != "Archived":  
return  
<br/>contract.status = "Closed"  
contract.close_out_date = frappe.utils.nowdate()  
contract.save(ignore_permissions=True)  
<br/>from kentender.contract_service import start_defect_liability_period  
start_defect_liability_period(contract.name)

That matches your close-out and DLP transition requirements cleanly.

**3\. Defect Liability Period workflow**

Your requirements say the system must:

- track DLP duration
- record defect notifications
- allow contract reopening if defects arise

This should not be just a date field. It needs an operational case workflow.

**Defect Liability Case states**

- Open
- Under Review
- Assigned
- Under Remedy
- Verified
- Closed
- Escalated

**Workflow definition**

{  
"workflow_name": "Defect Liability Case Workflow",  
"document_type": "Defect Liability Case",  
"is_active": 1,  
"workflow_state_field": "status",  
"states": \[  
{"state": "Open", "doc_status": 0},  
{"state": "Under Review", "doc_status": 0},  
{"state": "Assigned", "doc_status": 0},  
{"state": "Under Remedy", "doc_status": 0},  
{"state": "Verified", "doc_status": 0},  
{"state": "Closed", "doc_status": 0},  
{"state": "Escalated", "doc_status": 0}  
\]  
}

**Transitions**

\[  
{  
"state": "Open",  
"action": "Review Defect",  
"next_state": "Under Review",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Under Review",  
"action": "Assign Remedy",  
"next_state": "Assigned",  
"allowed": "Contract Implementation Team"  
},  
{  
"state": "Assigned",  
"action": "Start Remedy",  
"next_state": "Under Remedy",  
"allowed": "Supplier"  
},  
{  
"state": "Under Remedy",  
"action": "Verify Remedy",  
"next_state": "Verified",  
"allowed": "Inspection and Acceptance Committee"  
},  
{  
"state": "Verified",  
"action": "Close Defect Case",  
"next_state": "Closed",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Under Review",  
"action": "Escalate",  
"next_state": "Escalated",  
"allowed": "Accounting Officer"  
}  
\]

**Recommended DLP fields on Contract**

Add these if not already present:

\[  
{  
"dt": "Contract",  
"fieldname": "dlp_start_date",  
"fieldtype": "Date",  
"label": "DLP Start Date",  
"insert_after": "close_out_date"  
},  
{  
"dt": "Contract",  
"fieldname": "dlp_end_date",  
"fieldtype": "Date",  
"label": "DLP End Date",  
"insert_after": "dlp_start_date"  
},  
{  
"dt": "Contract",  
"fieldname": "dlp_status",  
"fieldtype": "Select",  
"options": "Not Started\\nActive\\nCompleted\\nReopened",  
"label": "DLP Status",  
"insert_after": "dlp_end_date"  
}  
\]

**DLP guards**

**A. Defect case only allowed when DLP is active or contract is reopened**

def validate_defect_case_allowed(doc):  
contract = frappe.get_doc("Contract", doc.contract)  
if contract.dlp_status not in ("Active", "Reopened"):  
frappe.throw("Defect Liability Case can only be opened during an active or reopened DLP.")

**B. DLP starts only after close-out**

def validate_dlp_start(contract):  
if contract.dlp_status == "Active" and not contract.close_out_date:  
frappe.throw("DLP cannot start before contract close-out.")

**C. Reopen contract if serious defect arises**

Your requirement explicitly allows contract reopening if defects arise.

def reopen_contract_for_defect(contract_name: str):  
contract = frappe.get_doc("Contract", contract_name)  
<br/>contract.dlp_status = "Reopened"  
contract.status = "Active"  
contract.save(ignore_permissions=True)  
contract.add_comment("Comment", "Contract reopened due to defect liability case.")

This should not happen automatically for every defect. I’d restrict it to:

- severity = High or Critical
- approved by Head of Procurement or Accounting Officer

**D. Complete DLP only when no open defect cases remain**

def validate_dlp_completion(contract):  
open_cases = frappe.db.get_value(  
"Defect Liability Case",  
{"contract": contract.name, "status": \["in", \["Open", "Under Review", "Assigned", "Under Remedy", "Escalated"\]\]},  
"name"  
)  
if open_cases:  
frappe.throw("Cannot complete DLP while defect cases remain open.")

**4\. Suggested hooks**

**hooks.py**

doc_events = {  
"Contract Variation": {  
"validate": "kentender.variation_workflow.validate_variation_rules",  
"on_update": "kentender.variation_workflow.handle_variation_events"  
},  
"Contract": {  
"validate": "kentender.closeout_workflow.validate_close_out_rules",  
"on_update": "kentender.closeout_workflow.handle_close_out_events"  
},  
"Defect Liability Case": {  
"validate": "kentender.dlp_workflow.validate_defect_case_rules",  
"on_update": "kentender.dlp_workflow.handle_defect_case_events"  
}  
}

**5\. Suggested module layout**

**variation_workflow.py**

def validate_variation_rules(doc, method=None):  
validate_variation_contract_state(doc)  
validate_variation_justification(doc)  
validate_variation_type_requirements(doc)  
<br/>def handle_variation_events(doc, method=None):  
if doc.status == "Implemented":  
implement_variation_effects(doc)

**closeout_workflow.py**

def validate_close_out_rules(doc, method=None):  
validate_close_out_final_acceptance(doc)  
validate_close_out_payments(doc)  
validate_close_out_handover(doc)  
validate_dlp_start(doc)  
<br/>def handle_close_out_events(doc, method=None):  
if doc.close_out_status == "Archived":  
finalize_contract_close_out(doc)

**dlp_workflow.py**

def validate_defect_case_rules(doc, method=None):  
validate_defect_case_allowed(doc)  
<br/>def handle_defect_case_events(doc, method=None):  
if doc.status == "Escalated":  
contract = frappe.get_doc("Contract", doc.contract)  
if doc.severity in ("High", "Critical"):  
reopen_contract_for_defect(contract.name)

**6\. What this gives you**

With these three workflows in place, your CLM now properly covers:

- controlled amendments during execution
- compliant close-out gates
- post-handover liability management
- contract reopening when serious defects arise

That is a big step toward matching your full Phase 2 contract management requirements.

**Best next move**

The remaining high-value workflow slice is:

**Claims + disputes + termination workflows**

That will complete the legal/governance wing of CLM.

Good. This is the last major governance block for CLM.

These three workflows belong together because your requirements define them as the **legal control layer** of contract management: claims by either side, staged dispute resolution, stop-work capability, and termination by Accounting Officer with documented justification.

**1\. Claim workflow**

Your requirements split claims into:

- **Claims by Procuring Entity**
    - liquidated damages
    - performance penalties
- **Claims by Contractor**
    - interest on delayed payments
    - compensation claims
    - variation claims

So the Claim workflow should handle both directions cleanly.

**States**

- Draft
- Submitted
- Under Review
- Recommended
- Approved
- Rejected
- Settled
- Escalated to Dispute

**Workflow definition**

{  
"workflow_name": "Claim Workflow",  
"document_type": "Claim",  
"is_active": 1,  
"workflow_state_field": "status",  
"states": \[  
{"state": "Draft", "doc_status": 0},  
{"state": "Submitted", "doc_status": 0},  
{"state": "Under Review", "doc_status": 0},  
{"state": "Recommended", "doc_status": 0},  
{"state": "Approved", "doc_status": 0},  
{"state": "Rejected", "doc_status": 0},  
{"state": "Settled", "doc_status": 0},  
{"state": "Escalated to Dispute", "doc_status": 0}  
\]  
}

**Transitions**

\[  
{  
"state": "Draft",  
"action": "Submit Claim",  
"next_state": "Submitted",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Draft",  
"action": "Submit Contractor Claim",  
"next_state": "Submitted",  
"allowed": "Supplier"  
},  
{  
"state": "Submitted",  
"action": "Start Review",  
"next_state": "Under Review",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Under Review",  
"action": "Recommend Decision",  
"next_state": "Recommended",  
"allowed": "Contract Implementation Team"  
},  
{  
"state": "Recommended",  
"action": "Approve Claim",  
"next_state": "Approved",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Recommended",  
"action": "Reject Claim",  
"next_state": "Rejected",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Approved",  
"action": "Settle Claim",  
"next_state": "Settled",  
"allowed": "Head of Finance"  
},  
{  
"state": "Under Review",  
"action": "Escalate to Dispute",  
"next_state": "Escalated to Dispute",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Recommended",  
"action": "Escalate to Dispute",  
"next_state": "Escalated to Dispute",  
"allowed": "Accounting Officer"  
}  
\]

**Required guards**

**A. Claim must belong to an active or suspended contract**

def validate_claim_contract_state(doc):  
contract = frappe.get_doc("Contract", doc.contract)  
if contract.status not in ("Active", "Suspended"):  
frappe.throw("Claims are only allowed for active or suspended contracts.")

**B. Required fields by claim type**

def validate_claim_type_requirements(doc):  
if not doc.claim_type:  
frappe.throw("Claim type is required.")  
if doc.claim_type in (  
"Liquidated Damages",  
"Performance Penalty",  
"Interest on Delayed Payment",  
"Compensation Claim",  
"Variation Claim"  
) and not doc.amount:  
frappe.throw("Claim amount is required for this claim type.")

**C. Procurement-entity claims can auto-calculate where applicable**

Your requirements say the system shall automatically calculate penalties where applicable.

def calculate_liquidated_damages(doc):  
if doc.claim_type != "Liquidated Damages" or doc.amount:  
return  
\# Replace with actual formula/policy  
contract = frappe.get_doc("Contract", doc.contract)  
overdue_days = max(0, \_get_contract_delay_days(contract))  
doc.amount = overdue_days \* 1000

**D. Variation claims should link back to Contract Variation where relevant**

def validate_variation_claim_link(doc):  
if doc.claim_type == "Variation Claim" and not doc.reference_variation:  
frappe.throw("Variation Claim must reference a Contract Variation.")

**2\. Dispute workflow**

Your requirements define the dispute lifecycle stages as:

- Notice of claim
- Negotiation
- Mediation
- Arbitration  
    and allow the Accounting Officer to issue **Stop Work Orders** based on advice from CIT and Head of Procurement.

**States**

- Notice of Claim
- Negotiation
- Mediation
- Arbitration
- Resolved
- Closed

**Workflow definition**

{  
"workflow_name": "Dispute Case Workflow",  
"document_type": "Dispute Case",  
"is_active": 1,  
"workflow_state_field": "current_stage",  
"states": \[  
{"state": "Notice of Claim", "doc_status": 0},  
{"state": "Negotiation", "doc_status": 0},  
{"state": "Mediation", "doc_status": 0},  
{"state": "Arbitration", "doc_status": 0},  
{"state": "Resolved", "doc_status": 0},  
{"state": "Closed", "doc_status": 0}  
\]  
}

**Transitions**

\[  
{  
"state": "Notice of Claim",  
"action": "Begin Negotiation",  
"next_state": "Negotiation",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Negotiation",  
"action": "Escalate to Mediation",  
"next_state": "Mediation",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Mediation",  
"action": "Escalate to Arbitration",  
"next_state": "Arbitration",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Negotiation",  
"action": "Resolve Dispute",  
"next_state": "Resolved",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Mediation",  
"action": "Resolve Dispute",  
"next_state": "Resolved",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Arbitration",  
"action": "Resolve Dispute",  
"next_state": "Resolved",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Resolved",  
"action": "Close Dispute",  
"next_state": "Closed",  
"allowed": "Head of Procurement"  
}  
\]

**Suggested field additions on Dispute Case**

You already have stop_work_order_issued, but I would add:

\[  
{  
"dt": "Dispute Case",  
"fieldname": "stop_work_reason",  
"fieldtype": "Small Text",  
"label": "Stop Work Reason",  
"insert_after": "stop_work_order_issued"  
},  
{  
"dt": "Dispute Case",  
"fieldname": "cit_recommendation",  
"fieldtype": "Small Text",  
"label": "CIT Recommendation",  
"insert_after": "stop_work_reason"  
},  
{  
"dt": "Dispute Case",  
"fieldname": "procurement_recommendation",  
"fieldtype": "Small Text",  
"label": "Head of Procurement Recommendation",  
"insert_after": "cit_recommendation"  
}  
\]

**Required guards**

**A. Dispute should usually reference a claim**

def validate_dispute_reference(doc):  
if not doc.claim:  
frappe.throw("Dispute Case must reference a Claim.")

**B. Stop Work Order only by Accounting Officer with recorded advice**

def validate_stop_work_order(doc):  
if doc.stop_work_order_issued:  
if "Accounting Officer" not in frappe.get_roles():  
frappe.throw("Only Accounting Officer can issue a Stop Work Order.")  
if not doc.cit_recommendation or not doc.procurement_recommendation:  
frappe.throw("Stop Work Order requires CIT and Head of Procurement recommendations.")

**C. Stop Work should suspend the contract**

def apply_stop_work_effect(doc):  
if doc.stop_work_order_issued:  
frappe.db.set_value("Contract", doc.contract, "status", "Suspended")

That gives you exactly the governance required by the FRS, without inventing a separate stop-work subsystem.

**3\. Termination workflow**

Your requirements are explicit:

- Accounting Officer may terminate contracts based on legal advice
- notice issued to supplier
- settlement of accounts
- site/property handover
- discharge documentation
- termination reason, supporting docs, final financial reconciliation must be recorded
- termination requires Accounting Officer approval and documented justification

So termination needs a serious workflow, not a button.

**States**

- Draft
- Under Legal Review
- Pending Accounting Officer Approval
- Approved
- Executed
- Cancelled

**Workflow definition**

{  
"workflow_name": "Termination Record Workflow",  
"document_type": "Termination Record",  
"is_active": 1,  
"workflow_state_field": "settlement_status",  
"states": \[  
{"state": "Draft", "doc_status": 0},  
{"state": "Under Legal Review", "doc_status": 0},  
{"state": "Pending Accounting Officer Approval", "doc_status": 0},  
{"state": "Approved", "doc_status": 0},  
{"state": "Executed", "doc_status": 0},  
{"state": "Cancelled", "doc_status": 0}  
\]  
}

That said, settlement_status is the wrong field to overload for workflow state. Better to add a dedicated field on Termination Record:

\[  
{  
"dt": "Termination Record",  
"fieldname": "workflow_state",  
"fieldtype": "Select",  
"options": "Draft\\nUnder Legal Review\\nPending Accounting Officer Approval\\nApproved\\nExecuted\\nCancelled",  
"label": "Workflow State",  
"insert_after": "contract"  
}  
\]

Then use that as the workflow field.

**Transitions**

\[  
{  
"state": "Draft",  
"action": "Send for Legal Review",  
"next_state": "Under Legal Review",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Under Legal Review",  
"action": "Forward for Approval",  
"next_state": "Pending Accounting Officer Approval",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Pending Accounting Officer Approval",  
"action": "Approve Termination",  
"next_state": "Approved",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Pending Accounting Officer Approval",  
"action": "Reject Termination",  
"next_state": "Cancelled",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Approved",  
"action": "Execute Termination",  
"next_state": "Executed",  
"allowed": "Head of Procurement"  
}  
\]

**Recommended additional fields on Termination Record**

\[  
{  
"dt": "Termination Record",  
"fieldname": "legal_advice_reference",  
"fieldtype": "Data",  
"label": "Legal Advice Reference",  
"insert_after": "termination_reason"  
},  
{  
"dt": "Termination Record",  
"fieldname": "notice_issued_to_supplier",  
"fieldtype": "Check",  
"label": "Notice Issued to Supplier",  
"insert_after": "legal_advice_reference"  
},  
{  
"dt": "Termination Record",  
"fieldname": "site_property_handover_completed",  
"fieldtype": "Check",  
"label": "Site/Property Handover Completed",  
"insert_after": "notice_issued_to_supplier"  
}  
\]

**Required guards**

**A. Termination requires documented reason**

def validate_termination_reason(doc):  
if not doc.termination_reason:  
frappe.throw("Termination reason is required.")

**B. Accounting Officer approval required before execution**

def validate_termination_execution(doc):  
if doc.workflow_state == "Executed":  
if not doc.approved_by:  
frappe.throw("Approved by is required before execution.")  
if "Accounting Officer" not in frappe.get_roles(doc.approved_by):  
frappe.throw("Termination must be approved by Accounting Officer.")

**C. Legal advice should exist before approval**

def validate_legal_review(doc):  
if doc.workflow_state in ("Pending Accounting Officer Approval", "Approved", "Executed"):  
if not doc.legal_advice_reference:  
frappe.throw("Legal advice reference is required before termination approval.")

**D. Execution requires operational closure evidence**

def validate_termination_operational_requirements(doc):  
if doc.workflow_state == "Executed":  
if not doc.notice_issued_to_supplier:  
frappe.throw("Supplier notice must be issued before executing termination.")  
if doc.settlement_status != "Completed":  
frappe.throw("Settlement of accounts must be completed before executing termination.")

**E. Executing termination updates the contract**

def execute_contract_termination(doc):  
if doc.workflow_state != "Executed":  
return  
<br/>contract = frappe.get_doc("Contract", doc.contract)  
contract.status = "Terminated"  
contract.save(ignore_permissions=True)  
contract.add_comment("Comment", f"Terminated via Termination Record {doc.name}.")

That maps tightly to your FRS without duplicating legal/accounting data.

**4\. Suggested hooks**

**hooks.py**

doc_events = {  
"Claim": {  
"validate": "kentender.claim_workflow.validate_claim_rules",  
"on_update": "kentender.claim_workflow.handle_claim_events"  
},  
"Dispute Case": {  
"validate": "kentender.dispute_workflow.validate_dispute_rules",  
"on_update": "kentender.dispute_workflow.handle_dispute_events"  
},  
"Termination Record": {  
"validate": "kentender.termination_workflow.validate_termination_rules",  
"on_update": "kentender.termination_workflow.handle_termination_events"  
}  
}

**claim_workflow.py**

def validate_claim_rules(doc, method=None):  
validate_claim_contract_state(doc)  
validate_claim_type_requirements(doc)  
validate_variation_claim_link(doc)  
calculate_liquidated_damages(doc)  
<br/>def handle_claim_events(doc, method=None):  
if doc.status == "Escalated to Dispute":  
existing = frappe.db.get_value("Dispute Case", {"claim": doc.name}, "name")  
if not existing:  
dispute = frappe.get_doc({  
"doctype": "Dispute Case",  
"contract": doc.contract,  
"claim": doc.name,  
"notice_date": frappe.utils.nowdate(),  
"current_stage": "Notice of Claim",  
"status": "Open",  
"summary": f"Auto-created from Claim {doc.name}"  
})  
dispute.insert(ignore_permissions=True)

**dispute_workflow.py**

def validate_dispute_rules(doc, method=None):  
validate_dispute_reference(doc)  
validate_stop_work_order(doc)  
<br/>def handle_dispute_events(doc, method=None):  
if doc.stop_work_order_issued:  
apply_stop_work_effect(doc)

**termination_workflow.py**

def validate_termination_rules(doc, method=None):  
validate_termination_reason(doc)  
validate_legal_review(doc)  
validate_termination_execution(doc)  
validate_termination_operational_requirements(doc)  
<br/>def handle_termination_events(doc, method=None):  
if doc.workflow_state == "Executed":  
execute_contract_termination(doc)

**5\. What this completes**

With these workflows in place, your CLM now has a full legal-governance wing covering:

- claims by both parties
- structured dispute escalation
- stop-work authority
- legally controlled termination

That closes most of the gap between a simple contract tracker and the public-procurement CLM your document actually requires.

**What remains after this**

At this point, the remaining high-value areas are:

- **CIT + Inspection Committee appointment workflows**
- **contract monitoring / dashboards / monthly report automation**
- **retention release automation**
- **integration blueprint conversion into actual importable files**

The smartest next move is:

**CIT + Inspection Committee appointment workflows**

because those roles are upstream of milestone verification, inspection, certification, disputes, and termination advice.

Good. These two workflows are foundational, not administrative side notes.

Why they matter: your requirements make both bodies formal control mechanisms, not ad hoc participant lists. The **Contract Implementation Team (CIT)** supervises implementation and milestone verification, while the **Inspection and Acceptance Committee** handles testing, validation, and acceptance decisions. That means their appointment workflow has to be controlled, auditable, and role-bound.

**1\. Design principle**

Do **not** model committee appointment as just “rows added to a table.”

Use:

- Contract Implementation Team Member as the appointment object for each member
- Inspection Committee Member as the appointment object for each member

This gives you:

- per-member approval status
- replacement/removal history
- clean audit trail
- role-based activation

That is the right level of control for your FRS.

**2\. CIT appointment workflow**

Your requirements say:

- Accounting Officer appoints the CIT
- members are recommended by Head of Procurement
- system captures member name, role, department, qualifications, member type

**States**

- Proposed
- Under Review
- Approved
- Active
- Removed
- Rejected

**Workflow field**

Use status on Contract Implementation Team Member.

**Workflow definition**

{  
"workflow_name": "CIT Member Appointment Workflow",  
"document_type": "Contract Implementation Team Member",  
"is_active": 1,  
"workflow_state_field": "status",  
"states": \[  
{"state": "Proposed", "doc_status": 0},  
{"state": "Under Review", "doc_status": 0},  
{"state": "Approved", "doc_status": 0},  
{"state": "Active", "doc_status": 0},  
{"state": "Removed", "doc_status": 0},  
{"state": "Rejected", "doc_status": 0}  
\]  
}

**Transitions**

\[  
{  
"state": "Proposed",  
"action": "Submit Recommendation",  
"next_state": "Under Review",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Under Review",  
"action": "Approve Appointment",  
"next_state": "Approved",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Under Review",  
"action": "Reject Appointment",  
"next_state": "Rejected",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Approved",  
"action": "Activate Member",  
"next_state": "Active",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Active",  
"action": "Remove Member",  
"next_state": "Removed",  
"allowed": "Accounting Officer"  
}  
\]

**Operational rule**

I recommend:

- Approved = formally appointed
- Active = actually assigned into current execution duties

That keeps appointment and operational activation separate, which is useful when the contract is not yet active.

**3\. CIT guards**

**A. Contract must exist and be in a valid state**

def validate_cit_contract_state(doc):  
contract = frappe.get_doc("Contract", doc.contract)  
if contract.status not in ("Pending Supplier Signature", "Pending Accounting Officer Signature", "Active", "Suspended"):  
frappe.throw("CIT members can only be appointed for contracts that are pending signature, active, or suspended.")

**B. Employee is required and should not be duplicated in same active team**

def validate_cit_duplicate_member(doc):  
existing = frappe.db.get_value(  
"Contract Implementation Team Member",  
{  
"contract": doc.contract,  
"employee": doc.employee,  
"status": \["in", \["Approved", "Active"\]\]  
},  
"name"  
)  
if existing and existing != doc.name:  
frappe.throw("Employee is already appointed to this contract's implementation team.")

**C. Required attributes**

def validate_cit_required_fields(doc):  
if not doc.member_type:  
frappe.throw("Member type is required.")  
if not doc.department:  
frappe.throw("Department is required.")

**D. Minimum team composition rule**

Because your member types include Chairperson, Member, Secretary, and Non-member Advisor, I recommend enforcing a minimum team composition before milestone verification is allowed:

- at least 1 Chairperson
- at least 1 Member
- optionally 1 Secretary depending on policy

def validate_cit_minimum_composition(contract_name):  
members = frappe.get_all(  
"Contract Implementation Team Member",  
filters={"contract": contract_name, "status": "Active"},  
fields=\["member_type"\]  
)  
member_types = \[m.member_type for m in members\]  
<br/>if "Chairperson" not in member_types:  
frappe.throw("Active CIT must include a Chairperson.")  
if "Member" not in member_types:  
frappe.throw("Active CIT must include at least one Member.")

This should be called before milestone transitions like Verified by CIT.

**4\. Inspection Committee appointment workflow**

Your requirements say:

- Head of Procurement recommends members
- system captures member name, role, qualification, department
- optional participants include Secretary and Technical Specialists

This is structurally similar to CIT but should remain separate because the authority and downstream permissions differ.

**States**

- Proposed
- Under Review
- Approved
- Active
- Dissolved
- Rejected

**Workflow definition**

{  
"workflow_name": "Inspection Committee Member Workflow",  
"document_type": "Inspection Committee Member",  
"is_active": 1,  
"workflow_state_field": "status",  
"states": \[  
{"state": "Proposed", "doc_status": 0},  
{"state": "Under Review", "doc_status": 0},  
{"state": "Approved", "doc_status": 0},  
{"state": "Active", "doc_status": 0},  
{"state": "Dissolved", "doc_status": 0},  
{"state": "Rejected", "doc_status": 0}  
\]  
}

**Transitions**

\[  
{  
"state": "Proposed",  
"action": "Submit Recommendation",  
"next_state": "Under Review",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Under Review",  
"action": "Approve Appointment",  
"next_state": "Approved",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Under Review",  
"action": "Reject Appointment",  
"next_state": "Rejected",  
"allowed": "Accounting Officer"  
},  
{  
"state": "Approved",  
"action": "Activate Committee Member",  
"next_state": "Active",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Active",  
"action": "Dissolve Appointment",  
"next_state": "Dissolved",  
"allowed": "Accounting Officer"  
}  
\]

**5\. Inspection Committee guards**

**A. Member uniqueness per contract**

def validate_inspection_duplicate_member(doc):  
existing = frappe.db.get_value(  
"Inspection Committee Member",  
{  
"contract": doc.contract,  
"employee": doc.employee,  
"status": \["in", \["Approved", "Active"\]\]  
},  
"name"  
)  
if existing and existing != doc.name:  
frappe.throw("Employee is already appointed to this contract's inspection committee.")

**B. Technical specialist rules**

Since your FRS explicitly allows technical specialists, I recommend requiring qualification when member_type = Technical Specialist.

def validate_inspection_specialist_qualification(doc):  
if doc.member_type == "Technical Specialist" and not doc.qualification:  
frappe.throw("Technical Specialist appointments require qualification details.")

**C. Minimum committee composition before milestone acceptance**

Before a milestone can move from Sent for Inspection to Accepted or Rejected, there should be an active inspection body.

Minimum recommended rule:

- at least 1 Chairperson
- at least 1 Member
- technical specialist optional depending on contract type

def validate_inspection_committee_composition(contract_name, require_technical=False):  
members = frappe.get_all(  
"Inspection Committee Member",  
filters={"contract": contract_name, "status": "Active"},  
fields=\["member_type"\]  
)  
member_types = \[m.member_type for m in members\]  
<br/>if "Chairperson" not in member_types:  
frappe.throw("Inspection Committee must include a Chairperson.")  
if "Member" not in member_types:  
frappe.throw("Inspection Committee must include at least one Member.")  
if require_technical and "Technical Specialist" not in member_types:  
frappe.throw("A Technical Specialist is required for this inspection.")

**6\. Downstream permission use**

These appointment workflows should not just exist for paperwork. They should drive permissions and validation in later workflows.

**CIT powers**

Only active CIT members should be treated as valid actors for:

- milestone verification
- implementation minutes
- site activity confirmation
- contract monitoring inputs

**Inspection Committee powers**

Only active inspection committee members should be treated as valid actors for:

- inspection records
- test validation
- acceptance / rejection decisions

This should be enforced by helper methods, not only by role names.

**Example**

def is_active_cit_member(user, contract_name):  
employee = frappe.db.get_value("Employee", {"user_id": user}, "name")  
if not employee:  
return False  
<br/>return bool(frappe.db.get_value(  
"Contract Implementation Team Member",  
{  
"contract": contract_name,  
"employee": employee,  
"status": "Active"  
},  
"name"  
))  
<br/><br/>def is_active_inspection_member(user, contract_name):  
employee = frappe.db.get_value("Employee", {"user_id": user}, "name")  
if not employee:  
return False  
<br/>return bool(frappe.db.get_value(  
"Inspection Committee Member",  
{  
"contract": contract_name,  
"employee": employee,  
"status": "Active"  
},  
"name"  
))

Then use these in milestone and certificate guards.

**7\. Workflow-linked automation**

**CIT activation automation**

When a Contract becomes Active, approved CIT members can be auto-promoted to Active.

def activate_approved_cit_members(contract_name):  
members = frappe.get_all(  
"Contract Implementation Team Member",  
filters={"contract": contract_name, "status": "Approved"},  
fields=\["name"\]  
)  
for m in members:  
frappe.db.set_value("Contract Implementation Team Member", m.name, "status", "Active")

**Inspection Committee activation automation**

When the first inspection is initiated, approved inspection committee members can be auto-promoted to Active.

def activate_approved_inspection_members(contract_name):  
members = frappe.get_all(  
"Inspection Committee Member",  
filters={"contract": contract_name, "status": "Approved"},  
fields=\["name"\]  
)  
for m in members:  
frappe.db.set_value("Inspection Committee Member", m.name, "status", "Active")

This keeps the workflows practical.

**8\. Suggested hooks**

**hooks.py**

doc_events = {  
"Contract Implementation Team Member": {  
"validate": "kentender.cit_workflow.validate_cit_rules",  
"on_update": "kentender.cit_workflow.handle_cit_events"  
},  
"Inspection Committee Member": {  
"validate": "kentender.inspection_committee_workflow.validate_inspection_committee_rules",  
"on_update": "kentender.inspection_committee_workflow.handle_inspection_committee_events"  
}  
}

**cit_workflow.py**

def validate_cit_rules(doc, method=None):  
validate_cit_contract_state(doc)  
validate_cit_duplicate_member(doc)  
validate_cit_required_fields(doc)  
<br/>def handle_cit_events(doc, method=None):  
pass

**inspection_committee_workflow.py**

def validate_inspection_committee_rules(doc, method=None):  
validate_inspection_duplicate_member(doc)  
validate_inspection_specialist_qualification(doc)  
<br/>def handle_inspection_committee_events(doc, method=None):  
pass

**9\. Recommended cross-workflow enforcement points**

Now that these appointment workflows exist, tighten the other workflows with them.

**Milestone verification**

Before Task can move to Verified by CIT:

- validate active CIT composition
- validate current user is active CIT member or allowed supervisory role

**Milestone acceptance / rejection**

Before Task can move from Sent for Inspection to Accepted/Rejected:

- validate active inspection committee composition
- validate current user is active inspection committee member or allowed supervisory role

**Dispute stop-work advice**

Before a Stop Work Order is issued on a Dispute Case:

- require recorded CIT recommendation
- require Head of Procurement recommendation
- allow Accounting Officer to act

That ties the whole CLM system together cleanly.

**10\. What this completes**

With these workflows added, your CLM now has formal governance around:

- who supervises implementation
- who verifies milestones
- who performs acceptance
- who can legitimately advise on disputes and termination

That is exactly what your requirements imply, and it closes an important structural gap.

**Best next move**

At this point, the remaining high-value pieces are:

- **monthly contract monitoring workflow and reports**
- **retention release workflow and reminders**
- **conversion of all defined workflows into import-ready JSON files and implementation scripts**

The smartest next step is:

**monthly contract monitoring + reporting automation**

because your FRS explicitly requires monthly monitoring reports with milestone progress, payment status, outstanding obligations, and contract risks.

Good. This is the right next slice because your FRS is explicit: the **Head of Procurement must prepare monthly contract monitoring reports**, and those reports must include **milestone progress, payment status, outstanding obligations, and contract risks**. You also require standard outputs like a **Contract Status Dashboard, Milestone Tracking Report, Payment Progress Report, Retention Schedule Report, Claims Register, Dispute Register, and Contract Close-Out Report**.

This should be built as **automation over ERPNext-native data + your custom CLM layer**, not as a manually filled report form.

**1\. Monitoring architecture**

**What should feed the monthly report**

**ERPNext-native sources**

- **Project / Task** → milestone progress
- **Purchase Invoice / Payment Entry** → payment status
- **Purchase Receipt / Quality Inspection** → delivery and acceptance evidence

**KenTender custom sources**

- **Contract** → lifecycle status
- **Acceptance Certificate** → certification status
- **Retention Ledger** → retained / released balances
- **Claim** → legal/financial claims
- **Dispute Case** → active disputes
- **Contract Variation** → pending or implemented changes
- **Defect Liability Case** → unresolved post-handover issues

That is the cleanest source model and matches your earlier ERPNext-aligned architecture.

**2\. New custom DocType: Monthly Contract Monitoring Report**

This should be the formal monthly snapshot record.

{  
"doctype": "DocType",  
"name": "Monthly Contract Monitoring Report",  
"module": "KenTender",  
"custom": 1,  
"is_submittable": 1,  
"fields": \[  
{ "fieldname": "contract", "fieldtype": "Link", "options": "Contract", "reqd": 1 },  
{ "fieldname": "company", "fieldtype": "Link", "options": "Company", "reqd": 1 },  
{ "fieldname": "report_month", "fieldtype": "Date", "reqd": 1 },  
{ "fieldname": "prepared_by", "fieldtype": "Link", "options": "User", "reqd": 1 },  
{ "fieldname": "prepared_on", "fieldtype": "Datetime" },  
<br/>{ "fieldname": "milestone_summary", "fieldtype": "Long Text" },  
{ "fieldname": "payment_summary", "fieldtype": "Long Text" },  
{ "fieldname": "outstanding_obligations", "fieldtype": "Long Text" },  
{ "fieldname": "contract_risks", "fieldtype": "Long Text" },  
<br/>{ "fieldname": "progress_percent", "fieldtype": "Percent" },  
{ "fieldname": "amount_invoiced", "fieldtype": "Currency" },  
{ "fieldname": "amount_paid", "fieldtype": "Currency" },  
{ "fieldname": "outstanding_amount", "fieldtype": "Currency" },  
{ "fieldname": "retention_balance", "fieldtype": "Currency" },  
<br/>{ "fieldname": "open_claims_count", "fieldtype": "Int" },  
{ "fieldname": "open_disputes_count", "fieldtype": "Int" },  
{ "fieldname": "open_defects_count", "fieldtype": "Int" },  
<br/>{ "fieldname": "overall_risk_level", "fieldtype": "Select", "options": "Low\\nMedium\\nHigh\\nCritical" }  
\]  
}

**Why this should exist**

You need a **formal monthly record**, not just a live dashboard. That supports auditability and management review, which your FRS emphasizes.

**3\. Workflow for monthly monitoring report**

Keep it lean.

**States**

- Draft
- Prepared
- Reviewed
- Submitted

**Transitions**

- Draft → Prepared  
    Head of Procurement
- Prepared → Reviewed  
    Accounting Officer or designated reviewer
- Reviewed → Submitted  
    Head of Procurement

This gives governance without making reporting unusably bureaucratic.

**4\. Report generation strategy**

Do not make users type everything from scratch.

**System-generated sections**

The system should auto-populate:

- milestone progress
- payment status
- retention balance
- claims/disputes counts
- contract risk indicators

**User-authored sections**

The Head of Procurement should add:

- narrative commentary
- mitigation actions
- escalations / recommendations

That gives the right balance between automation and accountable judgment.

**5\. Core aggregation logic**

**A. Milestone progress**

Source: Task where contract = &lt;contract&gt; and is_contract_milestone = 1

**Suggested computation**

- total milestones
- accepted milestones
- rejected milestones
- payment-eligible milestones
- overdue milestones

def get_milestone_metrics(contract_name):  
tasks = frappe.get_all(  
"Task",  
filters={"contract": contract_name, "is_contract_milestone": 1},  
fields=\["name", "milestone_status", "exp_end_date"\]  
)  
<br/>total = len(tasks)  
accepted = sum(1 for t in tasks if t.milestone_status == "Accepted")  
overdue = sum(  
1 for t in tasks  
if t.exp_end_date and t.exp_end_date < frappe.utils.nowdate()  
and t.milestone_status not in ("Accepted", "Payment Eligible")  
)  
<br/>progress = (accepted / total \* 100) if total else 0  
<br/>return {  
"total": total,  
"accepted": accepted,  
"overdue": overdue,  
"progress_percent": progress  
}

This maps directly to the required **milestone progress** section.

**B. Payment status**

Source:

- Purchase Invoice linked to Contract
- Payment Entry against those invoices

**Suggested computation**

- total invoiced
- total paid
- outstanding
- partial vs final payment status

def get_payment_metrics(contract_name):  
invoices = frappe.get_all(  
"Purchase Invoice",  
filters={"contract": contract_name, "docstatus": 1},  
fields=\["name", "grand_total", "outstanding_amount"\]  
)  
<br/>amount_invoiced = sum(float(i.grand_total or 0) for i in invoices)  
outstanding = sum(float(i.outstanding_amount or 0) for i in invoices)  
amount_paid = amount_invoiced - outstanding  
<br/>return {  
"amount_invoiced": amount_invoiced,  
"amount_paid": amount_paid,  
"outstanding_amount": outstanding  
}

This covers the required **payment status** section.

**C. Outstanding obligations**

This should not be a vague free-text field only.

Build it from:

- overdue milestones
- unpaid invoices
- pending certificates
- unreleased retention events due
- unresolved defect cases
- pending variations

def get_outstanding_obligations(contract_name):  
obligations = \[\]  
<br/>overdue_tasks = frappe.get_all(  
"Task",  
filters={  
"contract": contract_name,  
"is_contract_milestone": 1,  
"milestone_status": \["not in", \["Accepted", "Payment Eligible"\]\]  
},  
fields=\["name", "subject", "exp_end_date"\]  
)  
for t in overdue_tasks:  
if t.exp_end_date and t.exp_end_date < frappe.utils.nowdate():  
obligations.append(f"Overdue milestone: {t.subject}")  
<br/>unpaid = frappe.get_all(  
"Purchase Invoice",  
filters={"contract": contract_name, "docstatus": 1, "outstanding_amount": \[">", 0\]},  
fields=\["name"\]  
)  
for inv in unpaid:  
obligations.append(f"Outstanding payment on invoice: {inv.name}")  
<br/>open_defects = frappe.get_all(  
"Defect Liability Case",  
filters={"contract": contract_name, "status": \["in", \["Open", "Under Review", "Assigned", "Under Remedy", "Escalated"\]\]},  
fields=\["name"\]  
)  
for d in open_defects:  
obligations.append(f"Open defect case: {d.name}")  
<br/>return obligations

That gives a structured base for the **outstanding obligations** section.

**D. Contract risks**

Your FRS explicitly requires **contract risks** in the monthly monitoring report.

This should be system-assisted, not guessed manually.

**Suggested risk signals**

- overdue milestones
- rejected inspections
- high retention balance older than threshold
- open claims
- open disputes
- active suspension
- major variation pending
- severe defect cases

def get_contract_risks(contract_name):  
risks = \[\]  
<br/>contract = frappe.get_doc("Contract", contract_name)  
if contract.status == "Suspended":  
risks.append("Contract is suspended")  
<br/>overdue_count = frappe.db.count(  
"Task",  
{  
"contract": contract_name,  
"is_contract_milestone": 1,  
"exp_end_date": \["<", frappe.utils.nowdate()\],  
"milestone_status": \["not in", \["Accepted", "Payment Eligible"\]\]  
}  
)  
if overdue_count:  
risks.append(f"{overdue_count} overdue milestone(s)")  
<br/>open_claims = frappe.db.count("Claim", {"contract": contract_name, "status": \["not in", \["Settled", "Rejected"\]\]})  
if open_claims:  
risks.append(f"{open_claims} open claim(s)")  
<br/>open_disputes = frappe.db.count("Dispute Case", {"contract": contract_name, "status": \["in", \["Open", "In Progress"\]\]})  
if open_disputes:  
risks.append(f"{open_disputes} active dispute(s)")  
<br/>return risks

**Risk scoring**

I recommend a simple first-pass risk scoring:

- 0–1 signals → Low
- 2–3 → Medium
- 4–5 → High
- 6+ → Critical

**6\. Automation flow**

**When reports should be created**

Your FRS says monthly monitoring reports are required.

I recommend:

- auto-create a draft report on the **1st day of each month**
- for all **Active** and **Suspended** contracts
- prefill report fields with computed data

**Scheduler**

scheduler_events = {  
"monthly": \[  
"kentender.monitoring.create_monthly_contract_monitoring_reports"  
\]  
}

**Draft generation**

def create_monthly_contract_monitoring_reports():  
contracts = frappe.get_all(  
"Contract",  
filters={"status": \["in", \["Active", "Suspended"\]\]},  
fields=\["name", "company"\]  
)  
<br/>report_month = frappe.utils.get_first_day(frappe.utils.nowdate())  
<br/>for c in contracts:  
existing = frappe.db.get_value(  
"Monthly Contract Monitoring Report",  
{"contract": c.name, "report_month": report_month},  
"name"  
)  
if existing:  
continue  
<br/>report = build_monthly_report(c.name, c.company, report_month)  
report.insert(ignore_permissions=True)

**Builder**

def build_monthly_report(contract_name, company, report_month):  
milestone = get_milestone_metrics(contract_name)  
payment = get_payment_metrics(contract_name)  
obligations = get_outstanding_obligations(contract_name)  
risks = get_contract_risks(contract_name)  
retention_balance = get_contract_retention_balance(contract_name)  
<br/>return frappe.get_doc({  
"doctype": "Monthly Contract Monitoring Report",  
"contract": contract_name,  
"company": company,  
"report_month": report_month,  
"prepared_by": frappe.session.user if frappe.session.user != "Guest" else None,  
"prepared_on": frappe.utils.now_datetime(),  
"milestone_summary": f"Accepted {milestone\['accepted'\]} of {milestone\['total'\]} milestones. Overdue: {milestone\['overdue'\]}.",  
"payment_summary": f"Invoiced: {payment\['amount_invoiced'\]}, Paid: {payment\['amount_paid'\]}, Outstanding: {payment\['outstanding_amount'\]}.",  
"outstanding_obligations": "\\n".join(obligations),  
"contract_risks": "\\n".join(risks),  
"progress_percent": milestone\["progress_percent"\],  
"amount_invoiced": payment\["amount_invoiced"\],  
"amount_paid": payment\["amount_paid"\],  
"outstanding_amount": payment\["outstanding_amount"\],  
"retention_balance": retention_balance,  
"open_claims_count": frappe.db.count("Claim", {"contract": contract_name, "status": \["not in", \["Settled", "Rejected"\]\]}),  
"open_disputes_count": frappe.db.count("Dispute Case", {"contract": contract_name, "status": \["in", \["Open", "In Progress"\]\]}),  
"open_defects_count": frappe.db.count("Defect Liability Case", {"contract": contract_name, "status": \["in", \["Open", "Under Review", "Assigned", "Under Remedy", "Escalated"\]\]}),  
"overall_risk_level": score_risk_level(risks)  
})

**7\. Report outputs required by the FRS**

Your FRS also explicitly requires these reports:

- Contract Status Dashboard
- Milestone Tracking Report
- Payment Progress Report
- Retention Schedule Report
- Claims Register
- Dispute Register
- Contract Close-Out Report

Here’s the clean implementation path.

**A. Contract Status Dashboard**

Use ERPNext/Frappe Dashboard Charts + Number Cards.

**Core widgets**

- Active contracts
- Suspended contracts
- Contracts pending close-out
- Contracts in DLP
- High-risk contracts
- Open disputes
- Open claims

**B. Milestone Tracking Report**

Query report over Task:

- Contract
- Milestone
- Due date
- Status
- Overdue days
- Payment percentage

**C. Payment Progress Report**

Query report over Purchase Invoice + Payment Entry:

- Contract
- Invoiced amount
- Paid amount
- Outstanding amount
- Final payment pending yes/no

**D. Retention Schedule Report**

Query report over Retention Ledger:

- Contract
- Total retained
- Released
- Current balance
- Next release date
- Overdue release reminders

**E. Claims Register**

Query report over Claim:

- Contract
- Claim type
- Raised by
- Amount
- Status
- Escalated yes/no

**F. Dispute Register**

Query report over Dispute Case:

- Contract
- Claim
- Current stage
- Stop work issued
- Status

**G. Contract Close-Out Report**

Query report over Contract:

- Final acceptance issued
- Payments completed
- Handover completed
- DLP started
- Closed date

**8\. Reminder automation**

Your FRS explicitly mentions reminders for retention release.

You should also add reminders for monitoring/reporting.

**Recommended reminders**

- monthly report draft created
- report not submitted by a threshold date
- retention release due soon
- close-out readiness reached
- DLP nearing expiry

**Example scheduler**

scheduler_events = {  
"daily": \[  
"kentender.monitoring.send_retention_release_reminders",  
"kentender.monitoring.send_pending_monitoring_report_reminders"  
\],  
"monthly": \[  
"kentender.monitoring.create_monthly_contract_monitoring_reports"  
\]  
}

**9\. Suggested workflow for monitoring report**

**States**

- Draft
- Prepared
- Reviewed
- Submitted

**Transitions**

- Draft → Prepared  
    Head of Procurement
- Prepared → Reviewed  
    Accounting Officer
- Reviewed → Submitted  
    Head of Procurement

This is enough governance without making reporting painful.

**10\. What this gives you**

With this layer, you now have:

- mandatory monthly monitoring, as required by the FRS
- system-generated reporting from real ERPNext + KenTender data
- formal management snapshots for audit and governance
- dashboards and registers aligned to required outputs

That closes a major operational gap in the CLM design.

**Best next move**

The next logical step is:

**retention release workflow + reminder automation**

because that’s the remaining finance-control area specifically called out in your requirements and it ties directly into payment governance and monthly monitoring.

Good. This is the right next block.

Your requirements are clear that retention is not just an accounting number. The system must:

- **track retention balances**
- **schedule retention release**
- **send reminders when retention periods expire**
- **allow deductions during the retention period**

That means retention needs both:

1.  a **control workflow**
2.  **time-based automation**

**1\. Retention design principle**

Keep the Retention Ledger as the transaction source of truth, exactly as you approved.

That means:

- no separate retained-balance master record
- every movement is a ledger event
- summary is computed from ledger rows

**Retention event types**

Use the ledger for:

- Deduction
- Release
- Adjustment
- I also recommend adding:
    - Forfeiture

That gives you full coverage for the requirements and real-world enforcement.

**2\. Retention release workflow**

Since Retention Ledger is transaction-style, the workflow should govern **release events**, not the entire contract.

**Recommendation**

Add a dedicated custom DocType:

**Retention Release Request**

This is better than overloading Retention Ledger because:

- request/approval is different from actual financial posting
- reminders should target pending requests
- audit is cleaner

**Suggested DocType: Retention Release Request**

{  
"doctype": "DocType",  
"name": "Retention Release Request",  
"module": "KenTender",  
"custom": 1,  
"fields": \[  
{ "fieldname": "contract", "fieldtype": "Link", "options": "Contract", "reqd": 1 },  
{ "fieldname": "company", "fieldtype": "Link", "options": "Company", "reqd": 1 },  
{ "fieldname": "request_date", "fieldtype": "Date", "reqd": 1 },  
{ "fieldname": "eligible_release_date", "fieldtype": "Date", "reqd": 1 },  
{ "fieldname": "requested_amount", "fieldtype": "Currency", "reqd": 1 },  
{ "fieldname": "approved_amount", "fieldtype": "Currency" },  
{ "fieldname": "reason", "fieldtype": "Small Text" },  
{ "fieldname": "status", "fieldtype": "Select", "options": "Draft\\nPending Review\\nPending Approval\\nApproved\\nRejected\\nReleased", "reqd": 1 },  
{ "fieldname": "reviewed_by", "fieldtype": "Link", "options": "User" },  
{ "fieldname": "approved_by", "fieldtype": "Link", "options": "User" },  
{ "fieldname": "released_on", "fieldtype": "Date" },  
{ "fieldname": "retention_ledger_entry", "fieldtype": "Link", "options": "Retention Ledger" }  
\]  
}

This keeps the ledger clean and gives you a real workflow object.

**3\. Retention release workflow states**

**States**

- Draft
- Pending Review
- Pending Approval
- Approved
- Rejected
- Released

**Workflow definition**

{  
"workflow_name": "Retention Release Workflow",  
"document_type": "Retention Release Request",  
"is_active": 1,  
"workflow_state_field": "status",  
"states": \[  
{"state": "Draft", "doc_status": 0},  
{"state": "Pending Review", "doc_status": 0},  
{"state": "Pending Approval", "doc_status": 0},  
{"state": "Approved", "doc_status": 0},  
{"state": "Rejected", "doc_status": 0},  
{"state": "Released", "doc_status": 0}  
\]  
}

**Transitions**

\[  
{  
"state": "Draft",  
"action": "Submit for Review",  
"next_state": "Pending Review",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Pending Review",  
"action": "Forward for Approval",  
"next_state": "Pending Approval",  
"allowed": "Head of Procurement"  
},  
{  
"state": "Pending Approval",  
"action": "Approve Release",  
"next_state": "Approved",  
"allowed": "Head of Finance"  
},  
{  
"state": "Pending Approval",  
"action": "Reject Release",  
"next_state": "Rejected",  
"allowed": "Head of Finance"  
},  
{  
"state": "Approved",  
"action": "Execute Release",  
"next_state": "Released",  
"allowed": "Head of Finance"  
}  
\]

This fits your requirement that retention is tracked, released on schedule, and financially controlled.

**4\. Required release guards**

**A. Contract must be eligible for release**

Retention should not be releasable just because someone clicks a button.

def validate_retention_release_contract_state(doc):  
contract = frappe.get_doc("Contract", doc.contract)  
if contract.status not in ("Closed", "Active"):  
frappe.throw("Retention release is only allowed for active or closed contracts.")

I would allow Active because some contracts may release portions during phased completion, but your policy may narrow this later.

**B. Eligible release date must have been reached**

This directly supports the requirement to schedule retention release and remind when periods expire.

def validate_retention_release_date(doc):  
if doc.status in ("Pending Review", "Pending Approval", "Approved", "Released"):  
if doc.eligible_release_date > frappe.utils.nowdate():  
frappe.throw("Retention cannot be released before the eligible release date.")

**C. Requested amount cannot exceed available retained balance**

def validate_retention_release_amount(doc):  
balance = get_contract_retention_balance(doc.contract)  
if float(doc.requested_amount or 0) <= 0:  
frappe.throw("Requested retention release amount must be greater than zero.")  
if float(doc.requested_amount or 0) > balance:  
frappe.throw("Requested retention release amount exceeds retained balance.")

**D. Release cannot proceed if deductions are still unresolved**

Your requirements say deductions may be applied during the retention period.

I recommend a rule like this:

def validate_no_blocking_adjustments(doc):  
pending_adjustments = frappe.db.count(  
"Claim",  
{  
"contract": doc.contract,  
"status": \["in", \["Approved", "Recommended"\]\],  
"claim_type": \["in", \["Liquidated Damages", "Performance Penalty"\]\]  
}  
)  
if pending_adjustments and doc.status in ("Approved", "Released"):  
frappe.throw("Retention release is blocked by unresolved approved penalty-related claims.")

That ties retention control to the legal-financial layer cleanly.

**5\. Release execution logic**

When a release request reaches Released, it should generate a Retention Ledger row of type Release.

def execute_retention_release(doc):  
if doc.status != "Released":  
return  
<br/>if doc.retention_ledger_entry:  
return  
<br/>approved_amount = float(doc.approved_amount or doc.requested_amount or 0)  
if approved_amount <= 0:  
frappe.throw("Approved retention release amount must be greater than zero.")  
<br/>current_balance = get_contract_retention_balance(doc.contract)  
if approved_amount > current_balance:  
frappe.throw("Approved release amount exceeds retained balance.")  
<br/>new_balance = current_balance - approved_amount  
<br/>ledger = frappe.get_doc({  
"doctype": "Retention Ledger",  
"contract": doc.contract,  
"retention_type": "Release",  
"posting_date": doc.released_on or frappe.utils.nowdate(),  
"amount": approved_amount,  
"balance_after_transaction": new_balance,  
"release_date": doc.released_on or frappe.utils.nowdate(),  
"status": "Released",  
"remarks": f"Released via Retention Release Request {doc.name}"  
})  
ledger.insert(ignore_permissions=True)  
<br/>doc.db_set("retention_ledger_entry", ledger.name, update_modified=True)

That preserves the transaction-style model exactly as intended.

**6\. Reminder automation**

Your requirements explicitly call for **sending reminders when retention periods expire**.

There are two reminder types you should support:

**A. Pre-expiry reminder**

Example:

- send reminder 14 days before eligible release date
- send reminder 7 days before
- send reminder on due date

**B. Overdue reminder**

If eligible release date has passed and no release request exists or no release has been executed:

- send overdue reminder daily or weekly

**7\. Scheduler setup**

**hooks.py**

scheduler_events = {  
"daily": \[  
"kentender.retention_workflow.send_retention_release_reminders",  
"kentender.retention_workflow.send_overdue_retention_alerts"  
\]  
}

**8\. Reminder logic**

**A. Find contracts with retained balances and upcoming eligible releases**

You need a date basis. I recommend storing release_date or eligible_release_date either:

- on retention release request
- or derived from contract close-out / retention rules

For now, the simplest reliable model is:

- compute eligibility from contract close-out date plus retention terms
- or use explicit release requests with eligible_release_date

**Pre-due reminders**

def send_retention_release_reminders():  
today = frappe.utils.getdate()  
targets = frappe.get_all(  
"Retention Release Request",  
filters={  
"status": \["in", \["Draft", "Pending Review", "Pending Approval"\]\],  
"eligible_release_date": \["between", \[today, frappe.utils.add_days(today, 14)\]\]  
},  
fields=\["name", "contract", "eligible_release_date", "requested_amount"\]  
)  
<br/>for row in targets:  
\_notify_retention_due(row, overdue=False)

**Overdue reminders**

def send_overdue_retention_alerts():  
today = frappe.utils.getdate()  
overdue = frappe.get_all(  
"Retention Release Request",  
filters={  
"status": \["in", \["Draft", "Pending Review", "Pending Approval", "Approved"\]\],  
"eligible_release_date": \["<", today\]  
},  
fields=\["name", "contract", "eligible_release_date", "requested_amount"\]  
)  
<br/>for row in overdue:  
\_notify_retention_due(row, overdue=True)

**Notification helper**

def \_notify_retention_due(row, overdue=False):  
subject = f"Retention Release {'Overdue' if overdue else 'Upcoming'} for Contract {row.contract}"  
message = (  
f"Retention release request {row.name} for contract {row.contract} "  
f"is {'overdue' if overdue else 'due soon'}.\\n"  
f"Eligible release date: {row.eligible_release_date}\\n"  
f"Amount: {row.requested_amount}"  
)  
<br/>recipients = get_retention_notification_recipients(row.contract)  
if recipients:  
frappe.sendmail(recipients=recipients, subject=subject, message=message)

**Recipient helper**

def get_retention_notification_recipients(contract_name):  
\# Start simple: Head of Procurement + Head of Finance by role/email resolution  
users = set()  
<br/>for role in ("Head of Procurement", "Head of Finance"):  
role_users = frappe.get_all("Has Role", filters={"role": role}, fields=\["parent"\])  
for u in role_users:  
email = frappe.db.get_value("User", u.parent, "email")  
if email:  
users.add(email)  
<br/>return list(users)

**9\. Auto-create release requests**

A good usability improvement is to create draft Retention Release Request records automatically when retention becomes eligible.

**Suggested daily job**

def create_due_retention_release_requests():  
contracts = frappe.get_all(  
"Contract",  
filters={"status": "Closed"},  
fields=\["name", "company", "close_out_date"\]  
)  
<br/>for c in contracts:  
balance = get_contract_retention_balance(c.name)  
if balance <= 0:  
continue  
<br/>eligible_date = \_get_contract_retention_eligible_date(c.name)  
if not eligible_date:  
continue  
<br/>existing = frappe.db.get_value(  
"Retention Release Request",  
{"contract": c.name, "eligible_release_date": eligible_date, "status": \["!=", "Rejected"\]},  
"name"  
)  
if existing:  
continue  
<br/>if eligible_date <= frappe.utils.nowdate():  
frappe.get_doc({  
"doctype": "Retention Release Request",  
"contract": c.name,  
"company": c.company,  
"request_date": frappe.utils.nowdate(),  
"eligible_release_date": eligible_date,  
"requested_amount": balance,  
"status": "Draft",  
"reason": "Auto-created on retention eligibility date"  
}).insert(ignore_permissions=True)

This is exactly the kind of automation your FRS implies.

**10\. Retention schedule report**

Your FRS explicitly requires a **Retention Schedule Report**.

This should be a query/report over:

- Contract
- Retention Ledger
- Retention Release Request

**Suggested columns**

- Contract
- Supplier
- Total retained
- Current balance
- Eligible release date
- Release request status
- Days overdue
- Last reminder sent

That gives Finance and Procurement a clean operational view.

**11\. Recommended module structure**

**retention_workflow.py**

def validate_retention_release_rules(doc, method=None):  
validate_retention_release_contract_state(doc)  
validate_retention_release_date(doc)  
validate_retention_release_amount(doc)  
validate_no_blocking_adjustments(doc)  
<br/>def handle_retention_release_events(doc, method=None):  
if doc.status == "Released":  
execute_retention_release(doc)  
<br/>def send_retention_release_reminders():  
...  
<br/>def send_overdue_retention_alerts():  
...  
<br/>def create_due_retention_release_requests():  
...

**hooks.py**

doc_events = {  
"Retention Release Request": {  
"validate": "kentender.retention_workflow.validate_retention_release_rules",  
"on_update": "kentender.retention_workflow.handle_retention_release_events"  
}  
}  
<br/>scheduler_events = {  
"daily": \[  
"kentender.retention_workflow.create_due_retention_release_requests",  
"kentender.retention_workflow.send_retention_release_reminders",  
"kentender.retention_workflow.send_overdue_retention_alerts"  
\]  
}

**12\. What this completes**

With this in place, your CLM now supports:

- retained balance tracking
- scheduled release control
- reminder automation
- deductions / blocking adjustments
- clean ledger-based audit trail

That directly satisfies the retention-management part of your requirements.

**Best next move**

At this point, the most useful thing is no longer another isolated workflow. The highest-value next step is:

**Convert the full CLM design into an implementation pack**

- final DocType list
- final custom-field list
- final workflow inventory
- module ownership map
- coding sequence

That will give you a proper build blueprint instead of scattered design fragments.