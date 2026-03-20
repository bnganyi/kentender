# Governance Session ↔ Procurement CLM Adapter Pack

This pack adds a procurement integration layer between the generic Governance Session engine
and KenTender CLM objects.

## Included integrations
- CIT meeting → milestone verification support
- Inspection session → acceptance/rejection support
- Dispute session → stop-work recommendation support
- Monitoring review → risk/action escalation support

## Design principle
The adapter returns controlled outcomes and helper functions.
It does not blindly mutate downstream CLM records without explicit validation.
