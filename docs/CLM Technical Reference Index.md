# CLM Technical Reference Index

This directory contains module-focused technical documentation for KenTender CLM.

Use this index to find:
- Server-side rules (what gates what)
- Key fields to validate (data traceability)
- Whitelisted APIs used by the bench/UAT scripts

## Module docs (recommended order)
1. [`technical/clm-contract-signing-and-closeout.md`](technical/clm-contract-signing-and-closeout.md)
   - Contract signing activation
   - Closeout archive snapshot + edit lock

## UI entry point (for non-technical users)
- [`CLM UI User Guide`](CLM UI User Guide.md)

2. [`technical/clm-milestones-inspection-certificates-governance.md`](technical/clm-milestones-inspection-certificates-governance.md)
   - Milestone acceptance model
   - Governance Sessions auto-creation for proceedings
   - Inspection & certificates gating chain

3. [`technical/clm-invoices-payments-retention.md`](technical/clm-invoices-payments-retention.md)
   - Invoice certificate gate
   - Retention deduction and retention release readiness/execution

4. [`technical/clm-variations-claims-disputes-stopwork-and-termination.md`](technical/clm-variations-claims-disputes-stopwork-and-termination.md)
   - Variations + second-level approval for high-impact
   - Claims penalty/liquidated damages automation
   - Disputes + Stop Work issuance and contract suspension/resume
   - Termination evidence bundle enforcement + DLP + closeout integration

## Governance Sessions module (separate)
Governance Sessions have their own deeper docs:
- [`docs/governance_sessions_mvp.md`](governance_sessions_mvp.md)
- `clm-inputs/Procurement Proceedings Module - Functional Design.md` (functional design blueprint)

