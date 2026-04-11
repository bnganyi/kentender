# KenTender Hardening Specification Pack v1

**1\. Purpose**

This document defines the **complete enforcement model** required to transform KenTender from a functional system into a **controlled, auditable, production-grade procurement platform**.

It ensures:

- no invalid state transitions
- no workflow bypass
- strict role separation
- enforced strategy alignment
- template-driven execution
- financial integrity
- full traceability from policy to asset

**2\. Hardening Objectives**

The system must guarantee:

**Integrity**

- no invalid or inconsistent data states

**Control**

- no unauthorized actions or workflow bypass

**Isolation**

- users access only permitted data

**Traceability**

- every decision is auditable end-to-end

**Determinism**

- system behaves predictably under all scenarios

**3\. Hardening Architecture Layers**

**Layer 1 — Workflow Enforcement**

**Layer 2 — Permission & Assignment Enforcement**

**Layer 3 — Strategy Enforcement**

**Layer 4 — Template Enforcement**

**Layer 5 — Data Integrity Constraints**

**Layer 6 — Process Gating**

**Layer 7 — Financial Control**

**Layer 8 — Audit & Trace**

**Layer 9 — Separation of Duties**

**Layer 10 — UI Enforcement**

**4\. Workflow Enforcement**

**4.1 Immutable Workflow State**

**Rule**

No user may directly modify workflow state fields.

**Enforcement**

def validate(self):  
if self.has_value_changed("workflow_state") and not frappe.flags.in_workflow:  
frappe.throw("Workflow state can only be changed via workflow actions")

**Applies to**

- Requisition
- Plan
- Plan Item
- Tender
- Evaluation
- Award
- Contract
- Acceptance
- GRN

**4.2 Mandatory Workflow Completion**

Each stage must reach valid completion before downstream actions.

**Examples**

if not requisition.is_approved:  
frappe.throw("Requisition must be approved")  
<br/>if not plan_item.is_approved:  
frappe.throw("Plan item must be approved")

**5\. Permission & Assignment Enforcement**

**5.1 Assignment-Based Access**

**Rule**

Access to sensitive records requires explicit assignment.

**Applies to**

- Evaluation sessions
- Opening sessions
- Acceptance committees
- technical roles

**Enforcement**

def has_permission(doc, user):  
if doc.requires_assignment:  
if user not in doc.assigned_users:  
return False

**5.2 Supplier Isolation**

**Rule**

Suppliers can only access:

- their own bids
- published tenders

**Enforcement**

if user.role == "Supplier":  
return doc.supplier == user.supplier

**5.3 Sealed Bid Protection**

**Rule**

Before opening:

- no access to bid financials
- no access to documents

**Enforcement**

if doc.is_bid and not tender.is_opened:  
return False

**6\. Strategy Enforcement**

**6.1 Mandatory Strategy Linkage**

**Rule**

All transactional records must include:

- Program
- Sub-Program
- Indicator
- Target

**Enforcement**

if not self.target:  
frappe.throw("Target is mandatory")

**6.2 Cross-Stage Strategy Consistency**

**Rule**

Strategy must remain identical across the lifecycle.

**Enforcement**

assert plan_item.target == requisition.target  
assert tender.target == plan_item.target  
assert contract.target == tender.target  
assert asset.target == contract.target

**6.3 Strategy Hierarchy Validation**

**Rule**

Hierarchy must be valid.

if sub_program.program != program:  
frappe.throw("Invalid hierarchy")  
<br/>if indicator.sub_program != sub_program:  
frappe.throw("Invalid indicator linkage")

**7\. Template Enforcement**

**7.1 Template Selection**

**Rule**

Templates must be selected at planning stage.

**7.2 Template Lock**

**Rule**

Templates cannot change after plan approval.

if self.is_submitted and self.has_value_changed("template"):  
frappe.throw("Template cannot be changed after approval")

**7.3 Template Propagation**

**Rule**

Downstream stages must follow templates.

assert tender.template == plan_item.procurement_template

**7.4 Evaluation Template Enforcement**

**Rule**

Scoring structure must match template.

**8\. Data Integrity Constraints**

**8.1 Allocation Integrity**

if allocated_qty > requested_qty:  
frappe.throw("Over-allocation not allowed")

**8.2 Quantity Consistency**

assert grn.quantity <= contract.quantity  
assert assets.count == grn.quantity

**8.3 Score Integrity**

if score > max_score:  
frappe.throw("Score exceeds maximum")

**8.4 Supplier Consistency**

assert contract.supplier == award.supplier

**9\. Process Gating**

**9.1 Tender**

- requires approved plan item
- requires template

**9.2 Opening**

- requires submission deadline passed

**9.3 Evaluation**

- requires completed opening

**9.4 Award**

- requires approved evaluation

**9.5 Contract**

- requires award approval
- requires standstill completion

**9.6 GRN**

- requires acceptance

if not acceptance.is_approved:  
frappe.throw("Cannot create GRN before acceptance")

**9.7 Asset Creation**

- requires GRN

**10\. Financial Control**

**10.1 Reservation Control**

assert reservation <= budget.allocated

**10.2 Commitment Control**

assert commitment <= reservation

**10.3 Budget Balance**

available = allocated - reservation

**11\. Audit & Trace**

**11.1 Approval Logging**

Each approval must capture:

- user
- timestamp
- decision
- comment

**11.2 Override Logging**

Each override must capture:

- reason
- approver
- original value
- new value

**11.3 Immutable Records**

Deletion is prohibited for:

- bids
- evaluation results
- awards

**11.4 Full Trace Chain**

Asset  
→ GRN  
→ Contract  
→ Award  
→ Evaluation  
→ Opening  
→ Tender  
→ Plan Item  
→ Requisition  
→ Target  
→ Indicator  
→ Program  
→ Strategic Plan

**12\. Separation of Duties**

**Rules**

| **Conflict** | **Enforcement** |
| --- | --- |
| Supplier vs Evaluator | Block |
| Evaluator vs Contract Manager | Block |
| Inspector vs Storekeeper | Block |

**Enforcement**

- validation on assignment
- validation on action

**13\. Data Locking**

**Rule**

After submission:

- critical fields cannot change

if self.is_submitted:  
prevent_key_field_changes()

**14\. Edge Case Hardening**

**Partial Allocation**

- track remaining quantities

**Template Override**

- requires approval
- must log reason

**Failed Inspection**

- blocks acceptance

**Partial Delivery**

- allow multiple GRNs
- enforce totals

**Evaluation Tie**

- require manual resolution

**Supplier Complaint**

- must be linked to tender
- must follow workflow

**15\. UI Enforcement**

**Rules**

- hide sensitive data pre-stage
- disable fields post-approval
- status fields read-only

**16\. Verification Requirements**

System must fail if:

- workflow bypass occurs
- strategy mismatch exists
- financial inconsistency exists
- unauthorized access occurs
- trace chain is broken

**17\. Implementation Priority**

1.  Workflow enforcement
2.  Assignment enforcement
3.  Strategy enforcement
4.  Template enforcement
5.  Process gating
6.  Financial controls
7.  Audit logging

**Final Statement**

This document defines the **minimum enforcement required for a real procurement system**.

Without these controls:

- workflows can be bypassed
- data can be manipulated
- audit cannot be trusted

With these controls:

- the system becomes **deterministic, auditable, and production-ready**