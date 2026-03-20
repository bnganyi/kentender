
import frappe

def assign_tender_number(doc, method=None):
    if not doc.tender_number:
        # TODO: replace with naming series
        doc.tender_number = f"TND-{frappe.utils.now_datetime().strftime('%Y%m%d-%H%M%S')}"

def validate_tender(doc, method=None):
    if not doc.closing_datetime or not doc.opening_datetime:
        frappe.throw("Closing and opening datetimes are required.")
    if doc.opening_datetime < doc.closing_datetime:
        frappe.throw("Opening datetime cannot be earlier than closing datetime.")
    if doc.tender_status not in {"Draft", "Cancelled"}:
        # TODO: ensure at least one approved requisition link exists.
        pass
    # TODO: validate document pack completeness, evaluation scheme setup, and committee assignment.
