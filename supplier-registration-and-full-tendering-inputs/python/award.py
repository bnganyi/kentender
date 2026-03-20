
import frappe

def validate_award_decision(doc, method=None):
    if doc.award_status in {"Approved", "Finalized"} and not doc.approved_submission:
        frappe.throw("Approved submission is required before approving an award.")
    # TODO: validate recommendation linkage, challenge holds, and notification prerequisites.

def prepare_contract_handoff(award_decision_name):
    # TODO: create Award Contract Handoff or Award PO Handoff based on procurement profile.
    pass
