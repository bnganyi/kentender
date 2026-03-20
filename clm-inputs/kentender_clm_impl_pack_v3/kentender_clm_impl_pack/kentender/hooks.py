
doc_events = {
    "Contract": {
        "validate": "kentender.services.closeout_workflow.validate_close_out_rules",
        "on_update": "kentender.services.closeout_workflow.handle_close_out_events"
    },
    "Task": {
        "validate": "kentender.services.milestone_workflow.validate_task_milestone_rules",
        "on_update": "kentender.services.milestone_workflow.handle_task_milestone_events"
    },
    "Purchase Invoice": {
        "validate": "kentender.services.finance_integration.validate_purchase_invoice_certificate",
        "on_submit": "kentender.services.finance_integration.create_retention_ledger_entry_from_invoice",
    },
    "Contract Variation": {
        "validate": "kentender.services.variation_workflow.validate_variation_rules",
        "on_update": "kentender.services.variation_workflow.handle_variation_events"
    },
    "Claim": {
        "validate": "kentender.services.claim_workflow.validate_claim_rules",
        "on_update": "kentender.services.claim_workflow.handle_claim_events"
    },
    "Dispute Case": {
        "validate": "kentender.services.dispute_workflow.validate_dispute_rules",
        "on_update": "kentender.services.dispute_workflow.handle_dispute_events"
    },
    "Termination Record": {
        "validate": "kentender.services.termination_workflow.validate_termination_rules",
        "on_update": "kentender.services.termination_workflow.handle_termination_events"
    },
    "Defect Liability Case": {
        "validate": "kentender.services.dlp_workflow.validate_defect_case_rules",
        "on_update": "kentender.services.dlp_workflow.handle_defect_case_events"
    },
    "Contract Implementation Team Member": {
        "validate": "kentender.services.cit_workflow.validate_cit_rules",
        "on_update": "kentender.services.cit_workflow.handle_cit_events"
    },
    "Inspection Committee Member": {
        "validate": "kentender.services.inspection_committee_workflow.validate_inspection_committee_rules",
        "on_update": "kentender.services.inspection_committee_workflow.handle_inspection_committee_events"
    },
    "Retention Release Request": {
        "validate": "kentender.services.retention_workflow.validate_retention_release_rules",
        "on_update": "kentender.services.retention_workflow.handle_retention_release_events"
    }
}

scheduler_events = {
    "daily": [
        "kentender.services.contract_jobs.monitor_contract_expiry",
        "kentender.services.contract_jobs.monitor_dlp_expiry",
        "kentender.services.retention_workflow.create_due_retention_release_requests",
        "kentender.services.retention_workflow.send_retention_release_reminders",
        "kentender.services.retention_workflow.send_overdue_retention_alerts"
    ],
    "monthly": [
        "kentender.services.monitoring.create_monthly_contract_monitoring_reports"
    ]
}
