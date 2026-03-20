doc_events = {
    "Purchase Requisition": {
        "validate": "kentender.phase1_5.requisition.validate_requisition",
        "before_submit": "kentender.phase1_5.requisition.before_submit",
        "on_submit": "kentender.phase1_5.requisition.on_submit",
        "on_cancel": "kentender.phase1_5.requisition.on_cancel",
        "on_update_after_submit": "kentender.phase1_5.requisition.on_update_after_submit",
    },
    "Purchase Requisition Amendment": {
        "on_submit": "kentender.phase1_5.amendment.on_submit"
    }
}
