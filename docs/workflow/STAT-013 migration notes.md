# STAT-013 — Status standardization migration notes

## Goals

- Backfill **Purchase Requisition** `status` from **`workflow_state`** using `derive_purchase_requisition_summary_status` in `kentender/status_model/derived_status.py`.
- Set **legacy** `approval_status` = `workflow_state` for every row (hidden mirror; removes stale “Submitted vs Approved” pairs).

## Patch

- **`kentender.patches.v1_0.backfill_purchase_requisition_derived_status`** (see `patches.txt`) — runs `frappe.db.sql` updates in one shot; idempotent for consistent mappings.

## Rollback

- Restore from DB backup if needed; patch does not delete history. Re-running patch is safe.

## Verification

```sql
-- Expect 0 rows after patch on a healthy site
SELECT name, workflow_state, status, approval_status
FROM `tabPurchase Requisition`
WHERE IFNULL(workflow_state,'') != IFNULL(approval_status,'')
   OR status != CASE workflow_state
        WHEN 'Draft' THEN 'Draft'
        WHEN 'Submitted' THEN 'Pending'
        WHEN 'Under Review' THEN 'Pending'
        WHEN 'Approved' THEN 'Approved'
        WHEN 'Rejected' THEN 'Rejected'
        WHEN 'Cancelled' THEN 'Cancelled'
        ELSE status
     END;
```

(Adjust CASE if custom workflow states are added.)

## Developer checklist

- [ ] Run `bench migrate` after deploy.  
- [ ] Re-run minimal golden / UAT seed if environments depend on exact legacy tuples.  
- [ ] Update any external integrations that assumed `status` = literal "Submitted" for in-flight approvals — they should use **`workflow_state`** or **Pending** summary.
