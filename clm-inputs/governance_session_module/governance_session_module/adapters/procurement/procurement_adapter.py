import frappe
from frappe import _

PROCUREMENT_TEMPLATES = {
    "CIT Meeting": {
        "quorum_required": 2,
        "agenda": ["Milestone Progress Review", "Issues and Delays", "Recommendations"],
    },
    "Inspection Session": {
        "quorum_required": 2,
        "agenda": ["Inspection Findings", "Test Results", "Acceptance Decision"],
    },
    "Dispute Session": {
        "quorum_required": 2,
        "agenda": ["Claim Review", "Negotiation Position", "Escalation / Stop Work Recommendation"],
    },
    "Monitoring Review": {
        "quorum_required": 2,
        "agenda": ["Milestone Progress", "Payment Status", "Outstanding Obligations", "Contract Risks"],
    },
}

def create_procurement_session(title: str, session_type: str, reference_doctype: str, reference_name: str, meeting_date: str):
    template = PROCUREMENT_TEMPLATES.get(session_type)
    if not template:
        frappe.throw(_("Unknown procurement session type."))

    session = frappe.get_doc({
        "doctype": "Governance Session",
        "title": title,
        "context_type": "Procurement",
        "context_reference_doctype": reference_doctype,
        "context_reference_name": reference_name,
        "session_type": session_type,
        "meeting_date": meeting_date,
        "mode": "Physical",
        "quorum_required": template["quorum_required"],
        "minutes_status": "Draft",
        "status": "Draft",
    })
    session.insert(ignore_permissions=True)

    for idx, subject in enumerate(template["agenda"], start=1):
        frappe.get_doc({
            "doctype": "Session Agenda Item",
            "session": session.name,
            "sequence": idx,
            "subject": subject,
            "decision_required": 1,
        }).insert(ignore_permissions=True)

    return session.name

def procurement_resolution_unlocks(resolution_name: str):
    resolution = frappe.get_doc("Session Resolution", resolution_name)
    session = frappe.get_doc("Governance Session", resolution.session)
    if session.context_type != "Procurement" or resolution.status != "Approved":
        return None

    if resolution.resolution_type == "Recommend Variation":
        return {"unlock": "Contract Variation Review"}
    if resolution.resolution_type == "Recommend Stop Work":
        return {"unlock": "Dispute Stop Work Review"}
    if resolution.resolution_type == "Endorse Payment":
        return {"unlock": "Payment Certification"}
    if resolution.resolution_type in ("Recommend Acceptance", "Recommend Rejection"):
        return {"unlock": "Milestone Acceptance Review"}
    return {"unlock": "None"}
