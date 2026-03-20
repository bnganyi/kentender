KenTender Phase 1.5 Implementation Guide

Purpose
This package defines the public-sector Purchase Requisition / Demand Finalization module that sits between APP and Tender. It is the last internal gate before supplier-facing tendering begins.

Package contents
1. DocType starter JSON files.
2. Workflow JSON for the standard requisition path.
3. Python scaffolding for validation, commitments, amendments, and tender handoff.
4. Role-permission matrix and report catalog.
5. UAT checklist.

Recommended import order
1. Create custom roles used by the workflow.
2. Import DocTypes in this order:
   - Purchase Requisition Item
   - Purchase Requisition Approval
   - Purchase Requisition
   - Purchase Requisition Commitment
   - Purchase Requisition Exception
   - Purchase Requisition Amendment
   - Purchase Requisition Snapshot
   - Requisition Tender Handoff
3. Import the workflow.
4. Wire hooks and server methods into the KenTender app.
5. Bind budget and APP balance services.
6. Run UAT scenarios before production use.

Build notes
- The package is intentionally scaffolded, not production-complete.
- Budget availability logic is placeholder logic and must be connected to the entity's actual budget-control service.
- Anti-split detection is heuristic only and should be replaced with a stronger rules-based service.
- Approval routing is seeded with a default route and can later be matrix-driven.

Key policy behaviors
- Normal requisitions must be APP-linked.
- One-off and emergency requisitions require exceptions.
- Approval creates commitment records.
- Approved requisitions cannot be materially edited directly.
- Tender handoff is allowed only from approved requisitions.

Hardening checklist
- Add row-level permission filters by department and role.
- Replace placeholder APP balance lookup with production logic.
- Enforce approval-stage user assignment from Approval Matrix Rule.
- Add integration tests for cancellation, amendment, and tender handoff.
- Add notifications for aging requisitions and post-review deadlines.
