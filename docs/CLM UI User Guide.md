# CLM UI User Guide (What to do, where to click)

## Purpose
This guide helps non-developers operate KenTender’s Contract Lifecycle Management (CLM) by showing:
- what the system is doing for you,
- where to find the relevant records in the Desk,
- and what you typically need to do next when something is “blocked”.

This is intentionally UI-focused: it avoids field-level details.

## How the system “works in the background”
KenTender maintains an audit-ready chain of evidence across the contract lifecycle:
- milestones are tracked,
- inspections and acceptance decisions gate invoicing,
- payment and retention steps follow those acceptance decisions,
- legal/financial changes (variations, claims, disputes, stop work, termination) are controlled,
- and when a contract is closed, the system produces an immutable archive snapshot.

For key events, the system also creates a **Governance Session** (minutes/proceedings) so decisions are traceable and auditable.

## Where to find records (Desk navigation)
Use the Desk search bar (or the Doctype list pages) and type the document name. The relevant lists are typically:
- `Contract`
- `Task` (contract milestones)
- `Quality Inspection`
- `Inspection Report`
- `Acceptance Certificate`
- `Purchase Invoice`
- `Payment Entry`
- `Retention Ledger`
- `Contract Variation`
- `Claim`
- `Dispute Case`
- `Termination Record`
- `Governance Session`
- `Monthly Contract Monitoring Report`
- `Defect Liability Case`
- `Contract Closeout Archive`

If you are blocked, the “right next action” is almost always: update the certificate/decision evidence, complete required checklists, or follow a workflow transition step.

## Roles (practical view)
While role labels can vary by tenant, these are the most common responsibilities you’ll see:
- **Supplier / Contractor**: supplies confirmation and signature evidence; moves you forward at signature/confirmation points.
- **Accounting Officer**: approves/executes critical decisions and settlement completion steps.
- **Head of Procurement**: runs procurement review; manages committee evidence and monitoring reviews.
- **Head of Finance**: performs finance gates; handles special second-level approval where required.
- **System Manager**: can run controlled overrides for system governance.

## End-to-end user journey

### 1) Contract signatures → Contract becomes Active
In `Contract`, look for the status:
- `Pending Supplier Signature`: supplier side needs to sign/confirm.
- `Pending Accounting Officer Signature`: accounting officer side signs/approves.

Success:
- the contract becomes `Active` only after required signatures are complete.

### 2) Milestones (Tasks) → formal minutes (Governance Sessions)
Milestones are maintained as contract-linked `Task` records.
- When a milestone is marked ready/complete (with required confirmation), KenTender creates a `Governance Session` automatically.

Success:
- you’ll see a governance/minutes session appear that documents the milestone acceptance decision process.

Audit protection:
- when a Governance Session becomes `Locked`, it can’t be changed (so minutes/evidence remain immutable).

### 3) Inspection & acceptance → gate invoicing
The system expects an inspection chain before invoicing can proceed:
- `Quality Inspection`
- `Inspection Test Plan` (where applicable)
- `Inspection Report`
- `Acceptance Certificate`

In `Acceptance Certificate`, the key goal is:
- move the certificate to an **Issued** workflow state with the correct decision.

Success:
- invoicing is blocked unless the contract-linked certificate is in the correct issued decision state.

### 4) Invoices & payment governance → retention held in ledger
After certificates are issued:
- submit `Purchase Invoice` documents.

Success:
- retention is recorded in `Retention Ledger` (held until release conditions are met).

### 5) Retention release (only when it’s allowed)
Retention release is not a simple “approve” action:
- it is allowed only when closeout prerequisites are satisfied and DLP is completed,
- and additional legal/financial constraints can block release.

UI behavior:
- if release fails, the reason is usually explained via the system readiness/check output.

### 6) Contract variations, claims, disputes, and Stop Work
These are legal/financial change control records:

#### Contract Variation
- create a `Contract Variation` with justification.
- move it through review and decision.
- for high-impact variations, an extra finance-level approval may be required before it can reach `Approved`.

#### Claim
- create and advance `Claim` through procurement review and decision.
- penalty/liquidated damages claims are auto-calculated for traceability (where applicable).

#### Dispute Case & Stop Work
- create a `Dispute Case` and progress it through its lifecycle.
- if Stop Work is needed, the system requires recommendations before Stop Work issuance.
- when Stop Work is issued, the contract is suspended.
- once the last active Stop Work is withdrawn, the contract resumes the appropriate state.

Success:
- stop-work actions are controlled and supported by the governance/minutes proceedings.

### 7) Termination → settlement evidence bundle + DLP → closeout archive
Termination is handled via `Termination Record`.

Before settlement can be completed (set to `Completed`):
- ensure the termination evidence checklist items are set.

DLP:
- after handover prerequisites, DLP tracks the defect liability period and governs reopening if defects arise.

Closeout archive:
- when you close a contract, KenTender creates a `Contract Closeout Archive` snapshot and locks the closed contract from further edits.

## How to use Governance Sessions (minutes/proceedings)
You generally don’t create governance sessions manually—KenTender creates them automatically when key events occur.

What to look for:
- `Governance Session.status` (Draft → Under Review → Approved → Locked)
- quorum is required before sessions can move to approved/locked states
- resolutions/actions cannot advance if the parent session is not approved/locked

## “Blocked” situations: common patterns
If an action is rejected/blocked, check in this order:
1. Are the required inspection/certificate steps completed and in the right issued decision state?
2. Is the contract in the right lifecycle status (Active/Closed) for the action?
3. For termination: is the evidence checklist complete?
4. For retention release: is closeout + DLP completed and are there blocking legal/financial claims?
5. For variations: for high-impact changes, is the second-level approval completed?

