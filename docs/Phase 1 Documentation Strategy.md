# KenTender Phase 1 Documentation Strategy (Technical / UAT / Coverage)

## Goal
Create documentation that is:
- **Enforceable**: every gate/rule is traceable to code (hooks, validations, whitelisted APIs, workflows).
- **Testable**: each requirement has at least one UAT positive test and one negative test (where failure is meaningful).
- **Audit-friendly**: evidence chains and immutable logs are easy to locate during review.

## File Organization (mirrors CLM approach)
### 1) Technical Users (server-side, “what gates what”)
Use a dedicated module-focused technical doc per Phase 1 sub-area.
- `docs/Phase 1 Technical Reference Index.md` (entry point)
- `docs/technical/phase1-<module>.md` (module deep-dive)

Each module technical doc should include:
- Core DocTypes and what they represent in the governance chain
- Server-side enforcement points
  - DocType `validate` hooks
  - `on_submit` / `before_submit`
  - Whitelisted APIs used by bench/UAT
- Workflow / state machine rules (allowed transitions, required roles)
- Budget lifecycle and commitment rules (what status blocks what)
- Publication/locking/versioning rules (what is immutable and when)
- Anti-fragmentation controls (anti-split) and threshold method advisory logic
- Audit evidence model (which events are recorded and where)
- Where to check in Desk (one short “navigation cheat-sheet”)
- Known assumptions/gaps until Phase 1 requirements/code are fully synchronized

### 2) UAT (end-to-end validation, split by submodules)
Split UAT into module-focused documents for tractability.
- `docs/Phase 1 UAT Script.md` (index + preconditions)
- `docs/uat/phase1-uat-<n>-<slug>.md` (each module’s scenarios)

Each UAT module doc should include:
- Preconditions (bench/site, seeded masters, role setup, sample policy profiles)
- Positive path scenarios (expected final state changes)
- Negative path scenarios (expected blocking exceptions / forbidden transitions)
- Direct verification snippets where useful (SQL checks for balances/statuses)
- Suggested data you should set up once and reuse

### 3) Coverage & Traceability (requirement-to-code proof)
Maintain two lenses:
- **Master**: links full requirement set to implementation evidence
- **Checkpoint**: a condensed “current sprint” view (Covered/Partial/Gap)

Files:
- `docs/Phase 1 Coverage + Traceability (Master).md`
- `docs/Phase 1 Coverage Checkpoint Matrix.md`

Matrix requirements:
- Legend: `Covered`, `Partial`, `Gap`
- Requirement-to-Implementation table:
  - Requirement area / FRS/Wave item
  - Status
  - Code evidence (files + key functions + doctype hooks)
  - Main gaps / improvement target
- Reconciliation note (if user-provided traceability matrix differs from current code evidence)

## Update Workflow (how we will maintain these docs)
1. When you send updated requirements/design/code artifacts:
   - We update module technical docs first (rules/gates only).
2. Then we update UAT scenarios to match the new rules.
3. Finally, we update coverage matrices to keep “what we claim” aligned with “what exists”.

