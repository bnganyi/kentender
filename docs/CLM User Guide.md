# CLM User Guide (Technical-Operator)

## Purpose
This guide is for technical-operator users who need to understand the CLM gates and evidence chain (still in plain language, but oriented to exact system behavior).

It is written for non-developers (Procurement, Legal, Finance, and Committee users) who need to understand:
- What records are created
- What approvals and gates exist
- What “cannot happen” rules protect the procurement process

## What “governance” means in this system
Governance is the formal audit trail for legal/financial decisions.

When the system says a decision is “gated”, it means the workflow blocks progress unless required conditions are satisfied.

## Key record types you will see
- **Contract**: the commercial agreement with status changes (Draft -> Active -> Closed, etc.).
- **Milestones (Tasks)**: measurable contract phases that move through Pending -> Completed (with evidence rules).
- **Inspection Report + Certificates**: technical validation that gates invoicing.
- **Invoices + Payment Entry**: payment documents gated by accepted certificates.
- **Retention Ledger + Retention release**: retention balance, held until release criteria are met.
- **Contract Variation**: amendments requiring justification and approval.
- **Claim** and **Dispute Case**: formal legal/financial claims and dispute escalation.
- **Termination Record**: termination and settlement evidence checklist.
- **Governance Session (Minutes)**: formal minutes/proceedings for key events (automatically created).
- **Contract Closeout Archive**: immutable snapshot created at closure (audit protection).

## Roles you will typically need
Roles differ by tenant configuration, but in this system you will usually see these involved:
- **Supplier**: provides supplier-side confirmation and signature evidence.
- **Accounting Officer**: approves/executes decisions and issues some governance outcomes.
- **Head of Procurement**: runs procurement review and many committee-routing steps.
- **Head of Finance**: performs finance decision gates (including special second-level approval for high-impact variations).
- **System Manager**: can always proceed with governance transitions when needed for controlled override.

## End-to-end lifecycle (what to do)

The lifecycle below follows the Phase 2 FRS intent (contract signing → implementation → inspection/certification → invoicing/payments → retention → variations/claims/disputes/stop-work → termination + DLP → close-out + immutable archive).

### 1) Contract preparation and electronic signing (FRS 4.1 / 4.2)
1. The system creates a `Contract` after the tender is awarded.
2. **Supplier signature** is completed.
3. **Accounting Officer signature** is completed.
4. When both signatures are complete, the contract becomes **Active**.

What the system blocks:
- A contract cannot become `Active` until both required signatures are completed (and, if configured, required signature evidence exists).

Where to check:
- `Contract.status`

### 2) Implementation milestones and formal acceptance (FRS 4.4 / 4.5)
Milestones are tracked as `Task` rows on the contract.

User workflow:
1. Keep milestones in `Pending` until deliverables are ready.
2. When a milestone is ready, set:
   - `supplier_confirmed = 1`
   - `milestone_status = Completed`
3. The system automatically creates a `Governance Session` (minutes/proceedings) for that milestone.

What the system guarantees:
- Milestone completion triggers formal proceedings automatically.
- Once a governance session is **Locked**, it becomes immutable (minutes evidence, agenda items, and resolutions cannot be altered).

Where to check:
- `Task.milestone_status`
- `Governance Session.status`

### 3) Inspection, test plans, and certificates (FRS 4.6 / 4.7 / 4.8)
Before invoices can move forward, the contract must have the required inspection and certification chain.

User workflow (high level):
1. Ensure inspection artifacts exist and are submitted:
   - `Quality Inspection` (when required)
   - `Inspection Test Plan`
   - `Inspection Report`
2. Create/transition an `Acceptance Certificate` to the decision state that allows invoicing (Issued + Approved decision).

What the system blocks:
- Invoicing is blocked unless the contract-linked `Acceptance Certificate` is submitted and in the **Issued** workflow state.

Where to check:
- `Acceptance Certificate.workflow_state`
- `Acceptance Certificate.decision`

### 4) Invoices, payment governance, and retention deductions (FRS 4.9 / 4.10 / 4.12)

#### Invoices
User workflow:
1. Submit contract-linked invoices that reference the acceptance evidence you are relying on.

What the system blocks:
- `Purchase Invoice` processing is blocked unless it references an `Acceptance Certificate` that is submitted, in `Issued`, and has decision **Approved** for the same contract.

#### Retention deductions (retention is held)
What happens when you submit an invoice:
- Retention is deducted into the `Retention Ledger` (retention stays held until release rules are satisfied).

Where to check:
- `Retention Ledger` rows for your contract

### 5) Contract monitoring (FRS 4.13)
Monthly monitoring reports are prepared by the Head of Procurement and can create proceedings.

What users should do:
1. Generate monthly monitoring reports.
2. Move report status to `Reviewed` when the review is complete.

What the system does:
- A `Governance Session` is created for the monitoring review.

Where to check:
- `Monthly Contract Monitoring Report.status`
- `Governance Session.session_type = Monitoring Review`

### 6) Retention release (when it is financially allowed) (FRS 4.12 + penalty gating)
Retention release is only attempted after closeout and DLP are completed.

User workflow:
1. Ensure the contract is in the right closeout state.
2. Ensure the Defect Liability Period (DLP) is **completed**.
3. When ready, run retention release through the approved release path.

What the system blocks:
- Retention release is blocked if prerequisites are missing.
- Retention release is also blocked if there are unresolved **approved** penalty/LD claims that still need final settlement effect.

Where to check:
- `Contract.dlp_status`
- `Retention release readiness / blockers` output from the readiness API

### 7) Variations, claims, and disputes (including Stop Work) (FRS 4.14 / 4.15 / 4.16)

#### Variations (FRS 4.16)
User workflow:
1. Create a `Contract Variation` with:
   - justification
   - variation type (Scope Change / Time Extension / Cost Adjustment)
   - required impact fields (e.g., time extension days, financial impact)
2. Move it through review and decision.
3. For **high-impact** variations, complete the required extra approval before the variation can reach `Approved`.

What the system blocks:
- High-impact variations cannot reach `Contract Variation.status = Approved` unless the second-level approval is recorded.

Where to check:
- `Contract Variation.status`
- second-level approval flag fields (`second_level_approved`)

#### Claims (FRS 4.14)
User workflow:
1. Create the claim and move it through procurement review.
2. For penalty/liquidated-damages claim types created by the Procuring Entity:
   - the system deterministically calculates the penalty amount and stores trace inputs.

What the system guarantees:
- Penalty calculation is deterministic and traceable.
- Retention release is blocked if unresolved approved penalty claims exist.

Where to check:
- `Claim.amount`
- penalty trace fields (`penalty_*`)

#### Disputes and Stop Work orders (FRS 4.15)
User workflow:
1. Create a `Dispute Case` and move it through its lifecycle stages.
2. If Stop Work becomes necessary, Stop Work issuance requires:
   - CIT recommendation
   - Head of Procurement recommendation
   - issued by a role allowed for Stop Work issuance
3. When Stop Work is issued, the contract is suspended.
4. When the last active Stop Work is withdrawn, the contract resumes using the stored resume status (so other suspensions are not disturbed).

What the system guarantees:
- Stop Work cannot be issued without required recommendations.
- Contract suspension/resume behavior is overlap-safe for multiple disputes.

Where to check:
- `Dispute Case.stop_work_order_issued`
- `Contract.status` (Suspended/Active/Terminated/Closed as applicable)

### 8) Termination, DLP, and archive-grade closeout (FRS 4.17 / 4.18 / 4.19)

#### Termination evidence bundle enforcement (FRS 4.17)
User workflow:
1. Create a `Termination Record`.
2. Before settlement completion (`Completed`), ensure the evidence checklist is complete:
   - `legal_advice_reference`
   - `notice_issued_to_supplier`
   - `supporting_documents_provided`
   - `handover_completed`
   - `discharge_document_reference`

What the system blocks:
- Settlement completion cannot be set to `Completed` until the evidence checklist is satisfied.

#### DLP lifecycle (FRS 4.19)
After handover and closeout prerequisites:
- DLP manages defects tracking.
- The contract can be reopened when defects arise (governed route).

Where to check:
- `Contract.dlp_status`

#### Close-out archive and immutability (FRS 4.18)
When a contract is ready to close (closeout prerequisites satisfied), the system:
1. Creates a `Contract Closeout Archive` snapshot (immutable audit JSON).
2. Locks the operational contract so it cannot be edited while it remains `Closed`.

What the system guarantees:
- Every `Closed` contract has a corresponding immutable archive snapshot.
- Closed contracts are protected from accidental edits.

Where to check:
- `Contract.status = Closed`
- `Contract.closeout_archived = 1`
- `Contract.closeout_archive_ref`

## Governance Sessions: what you can expect
Governance Sessions are automatically created for key events (milestones, site handover, inspections, acceptance decisions, variation/claim/dispute decisions, Stop Work issuance, and monitoring review).

Key properties:
- **Quorum**: a minimum number of attendees are required before sessions can be approved/locked.
- **Minutes lifecycle**: Draft → Under Review → Approved → Locked.
- **Resolution gating**: a resolution cannot be approved if its parent session is still not approved/locked.
- **Locked immutability**: once Locked, the session and its linked items become immutable.

## Quick compliance checklist (non-technical)
- Contract becomes `Active` only after required signatures/evidence are complete.
- Invoices require an `Acceptance Certificate` that is submitted, in `Issued`, and **Approved**.
- Retention release requires:
  - closeout prerequisites
  - DLP completed
  - no unresolved approved penalty/LD claims
- High-impact variations require second-level approval before `Approved`.
- Stop Work requires CIT + Head of Procurement recommendations and triggers contract suspension/resume correctly.
- Termination settlement completion requires the legal/evidence checklist.
- Closing a contract creates an immutable closeout archive and locks edits.

## Where to look in the system
If you are validating audit readiness, check these places:
- `Contract`:
  - `status` (Active / Suspended / Terminated / Closed)
  - `dlp_status`
  - closeout archive fields (`closeout_archived`, `closeout_archive_ref`)
- `Task` milestones:
  - `milestone_status` and `supplier_confirmed`
- `Governance Session`:
  - minutes lifecycle (`status`) and immutability (`Locked`)
- `Session Resolution`:
  - resolution status and parent session gating
- `Acceptance Certificate`:
  - `workflow_state` = Issued and decision = Approved
- `Retention Ledger`:
  - held rows (deduction) and release rows
- `Claim`:
  - status and `penalty_*` trace fields for penalty/LD claims
- `Dispute Case`:
  - Stop Work fields and contract suspension effect
- `Termination Record`:
  - evidence checklist fields and `settlement_status`

