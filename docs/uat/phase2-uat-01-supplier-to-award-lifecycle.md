# Phase 2 UAT-01 - Supplier to Award Lifecycle

## Objective

Validate the full Phase 2 control chain:

`Supplier Registration -> Supplier Activation -> Tender Publication -> Submission Lock -> Evaluation Declaration Gate -> Award Decision -> Challenge Hold -> Award Handoff`

## Test Script

1. Create `Supplier Registration Application` in `Draft`.
2. Attach at least one `Supplier Compliance Document` with `Verified` status.
3. Move application to `Approved`; confirm `Supplier Master` sync and active status.
4. Create `Tender` from approved upstream lineage and add `Tender Document Pack`.
5. Progress Tender to `Published`.
6. Create `Tender Submission` from eligible supplier before deadline.
7. Force deadline pass and confirm lock behavior (`submission_status`, read-only, sealed).
8. Create `Evaluator Declaration` as `Signed`.
9. Create `Evaluation Worksheet`; verify no validation block.
10. Create `Award Recommendation`, then `Award Decision` as `Approved`.
11. Create `Challenge Review Case` as `Open`; verify `Finalized` award is blocked.
12. Resolve challenge; set `Award Decision` to `Finalized`.
13. Confirm `Award Contract Handoff` auto-created and Tender moved to award-published lifecycle.

## Expected Evidence

- Supplier eligibility hardening is enforced by status and verified document checks.
- Tender publication is blocked without document pack readiness.
- Submission gate enforces published tender + deadline + compliance.
- Evaluation requires signed declaration.
- Award finalization requires recommendation and can be held by active challenge.
- Finalized award creates traceable handoff artifact.

## Evidence Log (to append with live run IDs)

Fresh full-run evidence (2026-03-21):

- Supplier Registration Application: `SRA-2026-00057`
- Supplier Compliance Document: `5t28e1hup0` (`Verified`)
- Supplier Master: `SUPM-2026-00058` (`Active`, `Approved`)
- Tender: `TN-2026-00059` (progressed to `Award Published`)
- Tender Document Pack: `5t4l86ptlg` (`Approved`)
- Tender Submission: `TS-2026-00061`
- Evaluator Declaration: `EVD-2026-00062` (`Signed`)
- Evaluation Worksheet: `EVW-2026-00063`
- Award Recommendation: `AR-2026-00064`
- Award Decision: `AD-2026-00065` (`Finalized`)
- Challenge Review Case: `CRC-2026-00066`
- Award Contract Handoff: `ACH-2026-00067`
- Purchase Order generated at finalization: `PUR-ORD-2026-00013`

Control checks captured:

- Challenge hold worked as designed before finalization:
  - `Cannot finalize award while Challenge/Review Case is active: CRC-2026-00066`
- After challenge resolution, award finalization succeeded and produced handoff + PO lineage.
