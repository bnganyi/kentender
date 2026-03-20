from __future__ import annotations

doc_events = {
    "Procurement Plan": {
        "before_insert": "kentender_phase1.api.procurement_plan.before_insert",
        "validate": "kentender_phase1.api.procurement_plan.validate",
        "on_submit": "kentender_phase1.api.procurement_plan.on_submit",
        "on_update_after_submit": "kentender_phase1.api.procurement_plan.on_update_after_submit",
    },
    "Procurement Plan Item": {
        "validate": "kentender_phase1.api.procurement_plan_item.validate",
        "before_save": "kentender_phase1.api.procurement_plan_item.before_save",
        "on_update": "kentender_phase1.api.procurement_plan_item.on_update",
    },
    "Procurement Plan Revision": {
        "validate": "kentender_phase1.api.procurement_plan_revision.validate",
        "on_submit": "kentender_phase1.api.procurement_plan_revision.on_submit",
    },
    "Purchase Requisition": {
        "validate": "kentender_phase1.api.purchase_requisition.validate",
        "on_submit": "kentender_phase1.api.purchase_requisition.on_submit",
    },
}

scheduler_events = {
    "daily": [
        "kentender_phase1.scheduler.refresh_fragmentation_alerts",
        "kentender_phase1.scheduler.notify_stale_draft_plans",
        "kentender_phase1.scheduler.notify_unrequisitioned_approved_items",
    ]
}
