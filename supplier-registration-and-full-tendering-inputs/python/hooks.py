
doc_events = {
    "Supplier Registration Application": {
        "validate": "kentender_phase2.python.supplier.validate_supplier_application",
        "on_update_after_submit": "kentender_phase2.python.supplier.sync_supplier_master"
    },
    "Supplier Master": {
        "validate": "kentender_phase2.python.supplier.validate_supplier_master"
    },
    "Tender": {
        "validate": "kentender_phase2.python.tender.validate_tender",
        "before_save": "kentender_phase2.python.tender.assign_tender_number"
    },
    "Tender Submission": {
        "validate": "kentender_phase2.python.submission.validate_submission",
        "before_save": "kentender_phase2.python.submission.enforce_submission_lock"
    },
    "Evaluation Worksheet": {
        "validate": "kentender_phase2.python.evaluation.validate_worksheet"
    },
    "Award Decision": {
        "validate": "kentender_phase2.python.award.validate_award_decision"
    }
}
scheduler_events = {
    "daily": [
        "kentender_phase2.python.jobs.flag_expired_compliance",
        "kentender_phase2.python.jobs.auto_close_due_tenders",
        "kentender_phase2.python.jobs.notify_challenge_window_expiry",
    ]
}
