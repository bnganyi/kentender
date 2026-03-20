import frappe
from frappe import _
from kentender.services.contract_service import start_defect_liability_period

def validate_close_out_rules(doc, method=None):
    if getattr(doc, "close_out_status", None) in ("Ready for Close-Out","Under Final Review","Archived"):
        if not getattr(doc, "final_acceptance_certificate", None):
            frappe.throw(_("Final Acceptance Certificate is required for close-out."))
        if not getattr(doc, "handover_completed", 0):
            frappe.throw(_("Handover must be completed before close-out."))

def handle_close_out_events(doc, method=None):
    if getattr(doc, "close_out_status", None) == "Archived":
        doc.status = "Closed"
        doc.close_out_date = frappe.utils.nowdate()
        doc.save(ignore_permissions=True)
        start_defect_liability_period(doc.name)
