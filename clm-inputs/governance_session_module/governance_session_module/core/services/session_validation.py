import frappe
from frappe import _
from frappe.utils import now_datetime
import hashlib

def calculate_quorum_met(session_name: str) -> bool:
    session = frappe.get_doc("Governance Session", session_name)
    required = int(session.quorum_required or 0)
    if required <= 0:
        return True
    present = frappe.db.count("Session Participant", {
        "session": session.name,
        "attendance_status": ["in", ["Present", "Remote"]]
    })
    return present >= required

def validate_session_quorum(doc, method=None):
    if doc.status in ("Approved", "Locked"):
        met = calculate_quorum_met(doc.name) if doc.name else bool(doc.quorum_met)
        if not met:
            frappe.throw(_("Quorum not met. Cannot approve or lock session."))
        doc.quorum_met = 1

def validate_minutes_lock_requirements(doc, method=None):
    if doc.status == "Locked" and doc.minutes_status not in ("Approved", "Locked"):
        frappe.throw(_("Minutes must be approved before locking the session."))

def signature_hash_payload(session_name: str, signer: str, signer_role: str, target_type: str, target_name: str = "") -> str:
    raw = f"{session_name}|{signer}|{signer_role}|{target_type}|{target_name}|{now_datetime()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

@frappe.whitelist()
def sign_session_item(session_name: str, signer_role: str, target_type: str, target_name: str = "", method_name: str = "OTP"):
    sig_hash = signature_hash_payload(session_name, frappe.session.user, signer_role, target_type, target_name)
    sig = frappe.get_doc({
        "doctype": "Session Signature",
        "session": session_name,
        "signer": frappe.session.user,
        "signer_role": signer_role,
        "signature_target_type": target_type,
        "target_name": target_name,
        "signature_method": method_name,
        "signature_hash": sig_hash,
        "signed_at": now_datetime(),
        "verification_status": "Verified",
    })
    sig.insert(ignore_permissions=True)
    if target_type == "Attendance" and target_name:
        frappe.db.set_value("Session Participant", target_name, {
            "signed_attendance": 1,
            "signature_status": "Signed",
        })
    return sig.name

def validate_resolution_requires_approved_session(doc, method=None):
    session_status = frappe.db.get_value("Governance Session", doc.session, "status")
    if doc.status in ("Approved", "Implemented", "Closed") and session_status not in ("Approved", "Locked"):
        frappe.throw(_("Session must be approved before resolution can move forward."))
