import frappe
from frappe import _

def get_procurement_unlock(resolution_name: str):
    resolution = frappe.get_doc("Session Resolution", resolution_name)
    session = frappe.get_doc("Governance Session", resolution.session)

    if session.context_type != "Procurement":
        return None

    ref_doctype = None
    ref_name = None
    if resolution.agenda_item:
        agenda = frappe.get_doc("Session Agenda Item", resolution.agenda_item)
        ref_doctype = agenda.reference_doctype
        ref_name = agenda.reference_name

    mapping = {
        ("CIT Meeting", "Recommend Approval", "Task"): "Milestone Verification Review",
        ("Inspection Session", "Recommend Acceptance", "Task"): "Milestone Acceptance Review",
        ("Inspection Session", "Recommend Rejection", "Task"): "Milestone Rejection Review",
        ("Dispute Session", "Recommend Stop Work", "Dispute Case"): "Stop Work Review",
        ("Monitoring Review", "Escalate", "Monthly Contract Monitoring Report"): "Risk Escalation Review",
        ("Monitoring Review", "Endorse Payment", "Purchase Invoice"): "Payment Certification",
    }

    unlock = mapping.get((session.session_type, resolution.resolution_type, ref_doctype))
    if not unlock:
        return None

    return {
        "unlock": unlock,
        "reference_doctype": ref_doctype,
        "reference_name": ref_name,
        "session": session.name,
        "resolution": resolution.name
    }

def validate_cit_session_supports_task(session_name: str):
    session = frappe.get_doc("Governance Session", session_name)
    if session.context_type != "Procurement" or session.session_type != "CIT Meeting":
        frappe.throw(_("Session is not a procurement CIT meeting."))
    return True

def cit_recommendation_for_task(task_name: str, session_name: str):
    validate_cit_session_supports_task(session_name)
    session = frappe.get_doc("Governance Session", session_name)

    approved = frappe.db.get_value(
        "Session Resolution",
        {"session": session.name, "status": "Approved"},
        "name"
    )
    if not approved:
        frappe.throw(_("Approved session resolution is required before using CIT recommendation."))

    return {
        "task": task_name,
        "session": session.name,
        "supports": "Verified by CIT transition"
    }

def inspection_recommendation_for_task(task_name: str, session_name: str):
    session = frappe.get_doc("Governance Session", session_name)
    if session.context_type != "Procurement" or session.session_type != "Inspection Session":
        frappe.throw(_("Session is not a procurement inspection session."))

    approved_resolutions = frappe.get_all(
        "Session Resolution",
        filters={"session": session.name, "status": "Approved"},
        fields=["name", "resolution_type"]
    )
    if not approved_resolutions:
        frappe.throw(_("Approved inspection resolution is required."))

    return {
        "task": task_name,
        "session": session.name,
        "recommendations": approved_resolutions
    }

def dispute_stop_work_support(dispute_case: str, session_name: str):
    session = frappe.get_doc("Governance Session", session_name)
    if session.context_type != "Procurement" or session.session_type != "Dispute Session":
        frappe.throw(_("Session is not a procurement dispute session."))

    resolution = frappe.db.get_value(
        "Session Resolution",
        {"session": session.name, "status": "Approved", "resolution_type": "Recommend Stop Work"},
        "name"
    )
    if not resolution:
        frappe.throw(_("Approved stop-work recommendation is required."))

    return {
        "dispute_case": dispute_case,
        "session": session.name,
        "supports": "Accounting Officer stop-work review"
    }

def monitoring_review_escalations(report_name: str, session_name: str):
    session = frappe.get_doc("Governance Session", session_name)
    if session.context_type != "Procurement" or session.session_type != "Monitoring Review":
        frappe.throw(_("Session is not a procurement monitoring review."))

    actions = frappe.get_all(
        "Session Action",
        filters={"session": session.name, "status": ["in", ["Open", "In Progress"]]},
        fields=["name", "description", "assigned_to", "due_date", "status"]
    )
    resolutions = frappe.get_all(
        "Session Resolution",
        filters={"session": session.name, "status": "Approved"},
        fields=["name", "resolution_type", "resolution_text"]
    )

    return {
        "report": report_name,
        "session": session.name,
        "open_actions": actions,
        "approved_resolutions": resolutions
    }
