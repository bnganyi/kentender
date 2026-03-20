# Governance Session Module v3 Deployment Notes

## What changed from v2
- Added adapter-based architecture
- Added procurement adapter
- Added procurement session templates
- Preserved generic core engine

## Recommended install order
1. Import core DocTypes
2. Apply core workflows
3. Add core services
4. Configure real roles/permissions
5. Add adapter templates
6. Test procurement adapter flows

## Validation checklist
- Create generic Governance Session
- Create procurement session from adapter
- Verify template agenda items are created
- Add participants and verify quorum
- Approve session, approve resolution
- Confirm adapter returns expected unlock behavior
