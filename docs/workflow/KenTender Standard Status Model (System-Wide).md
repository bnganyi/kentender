# KenTender Standard Status Model (System-Wide)

**Objective**

Define a **consistent, non-overlapping status architecture** across all DocTypes that:

- removes ambiguity
- enforces backend control
- aligns with workflow engine
- supports audit and reporting
- prevents field duplication and drift

**1\. The 3-Layer Status Model (Final Standard)**

Every approval-controlled DocType must follow this structure:

**Layer 1 — System Lifecycle (Frappe)**

**Field: docstatus**

| **Value** | **Meaning** |
| --- | --- |
| 0   | Draft (editable) |
| 1   | Submitted (locked for normal edits) |
| 2   | Cancelled |

**Rules**

- Controlled by Frappe
- NEVER used for business workflow logic
- NEVER extended with custom meanings

**Layer 2 — Business Workflow (PRIMARY)**

**Field: workflow_state**

👉 This is the **ONLY authoritative business state**

**Examples (Requisition)**

- Draft
- Pending HOD Approval
- Pending Finance Approval
- Approved
- Rejected
- Returned for Amendment

**Rules**

- Controlled ONLY by workflow engine services
- NEVER manually edited
- ALWAYS reflects current business stage
- MUST drive:
    - permissions
    - UI buttons
    - report filtering
    - next actions

**Layer 3 — Derived Status (OPTIONAL)**

**Field: status (or approval_status if needed)**

👉 This is a **derived summary field**

**Purpose**

- simplify reporting
- simplify dashboards
- give high-level state (Pending / Approved / Rejected)

**Example mapping**

| **Workflow State** | **Status** |
| --- | --- |
| Draft | Draft |
| Pending HOD Approval | Pending |
| Pending Finance Approval | Pending |
| Approved | Approved |
| Rejected | Rejected |
| Returned for Amendment | Pending |

**Critical rule**

❗ status must NEVER contain information not already implied by workflow_state

**2\. What to REMOVE or FIX immediately**

From your current system:

**Problem fields**

- Status (used ambiguously)
- Approval Status (duplicate meaning)

**Fix strategy**

**Step 1 — Rename clearly**

Use:

- docstatus → internal only
- workflow_state → main UI field
- status → optional derived

**Step 2 — Remove duplication**

👉 If approval_status == workflow_state meaning

Then:

- REMOVE approval_status

OR

- convert to computed/read-only

**3\. Field Behavior Rules (STRICT)**

**3.1 workflow_state**

- read-only on UI
- updated ONLY via workflow services
- cannot be edited via:
    - form
    - import
    - patch
    - client script

**3.2 status (derived)**

- read-only
- auto-computed on save or via service
- NEVER user-editable

**3.3 docstatus**

- controlled via submit/cancel
- never overridden for business logic

**4\. UI Standard (VERY IMPORTANT)**

**Replace confusing fields with this layout:**

**Recommended display**

- **Lifecycle:** Submitted
- **Stage:** Pending Finance Approval
- **Overall Status:** Pending

**Do NOT show:**

- 3 editable dropdowns
- duplicated meanings
- conflicting values

**5\. Standard Mapping Pattern**

**Define per DocType:**

workflow_state → status

**Example (Requisition)**

Draft → Draft  
Submitted → Pending  
Pending HOD Approval → Pending  
Pending Finance Approval → Pending  
Approved → Approved  
Rejected → Rejected  
Returned → Pending

**This mapping must be:**

- centralized
- consistent
- not scattered across scripts

**6\. System-wide consistency rules**

Every DocType must follow:

| **Field** | **Purpose** | **Editable** |
| --- | --- | --- |
| docstatus | system lifecycle | system only |
| workflow_state | business state | ❌   |
| status | derived summary | ❌   |

**7\. Anti-patterns (must avoid)**

**❌ Multiple “status” fields**

- status
- approval_status
- workflow_status
- lifecycle_status

👉 Leads to drift and bugs

**❌ Editable workflow fields**

Users should NEVER change state manually

**❌ Business logic tied to docstatus**

This is a common mistake in Frappe systems

**❌ Report filtering on wrong field**

Always filter on:

- workflow_state  
    NOT:
- status  
    NOT:
- docstatus

**8\. Migration plan (for your current system)**

**Step 1 — Audit all DocTypes**

List:

- status fields
- approval fields
- workflow fields

**Step 2 — Classify each field**

- keep
- convert to derived
- delete

**Step 3 — Implement mapping**

Centralize:

- workflow_state → status

**Step 4 — Lock fields**

- set read-only
- enforce backend protection (WF-002)

**Step 5 — Update reports**

Ensure all reports use:

- workflow_state

**Step 6 — Fix UI**

Remove confusing duplicates

**9\. Example: Your current PR (corrected)**

**Current (problematic)**

- Status = Submitted
- Workflow State = Approved
- Approval Status = Approved

**Corrected**

- Lifecycle: Submitted
- Stage: Approved
- Status: Approved (derived)

OR even better:

👉 Hide Status entirely and show:

- **Stage: Approved**

**10\. Design principle to enforce**

One field = one meaning

If two fields mean the same thing:  
👉 one must go

**11\. What this unlocks**

After standardization:

- cleaner UI
- consistent reports
- fewer permission bugs
- easier workflow debugging
- reliable audit trails
- simpler developer mental model

**Implementation:** [STAT Implementation Tracker](STAT%20Implementation%20Tracker.md) and [KenTender Status Standard — Developer Framework](KenTender%20Status%20Standard%20%E2%80%94%20Developer%20Framework.md).