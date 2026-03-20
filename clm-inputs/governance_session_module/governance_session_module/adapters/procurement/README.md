# Procurement Adapter for Governance Session

This adapter maps Governance Session into procurement-specific uses without hardcoding procurement into the core engine.

## Supported procurement session templates
- Tender Evaluation Meeting
- CIT Meeting
- Site Meeting
- Inspection Session
- Acceptance Committee Sitting
- Variation Review
- Claims Review
- Dispute Session
- Termination Review
- Monitoring Review

## Context conventions
- context_type = Procurement
- context_reference_doctype = Tender / Contract / Task / Claim / Dispute Case / Contract Variation / Termination Record / Monthly Contract Monitoring Report
- context_reference_name = linked record name

## Integration intent
Approved procurement resolutions should usually unlock downstream procurement steps rather than auto-execute them blindly.
