
import frappe

def validate_worksheet(doc, method=None):
    declaration = frappe.db.exists("Evaluator Declaration", {
        "tender": doc.tender,
        "committee_member": doc.evaluator,
        "status": ["in", ["Signed", "Both", "COI", "Confidentiality"]]
    })
    if not declaration:
        frappe.throw("Evaluator declaration must be signed before evaluation starts.")
    # TODO: enforce stage separation and access control between preliminary, technical, and financial stages.

def aggregate_consensus(tender):
    # TODO: consolidate completed worksheets into Evaluation Consensus Record without overwriting evaluator evidence.
    pass
