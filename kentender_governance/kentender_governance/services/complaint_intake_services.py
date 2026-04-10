# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""GOV-STORY-021: complaint intake (submit) and admissibility review + withdrawal + status events."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime, today

from kentender_governance.services.complaint_service_utils import (
	append_complaint_event,
	ensure_complaint_not_locked,
	get_complaint_doc,
	norm,
	save_complaint,
)

C = "Complaint"

_ADM_OUTCOMES = frozenset({"Admissible", "Inadmissible", "Deferred"})
_COMPLAINT_TYPES = frozenset({"Procurement Process", "Award", "Contract", "Other"})
_COMPLAINANT_TYPES = frozenset({"Bidder", "Supplier", "Citizen", "Other"})


def _ensure_can_intake_transition(doc: Document) -> None:
	st = norm(doc.status)
	if st in ("Closed", "Withdrawn", "Decided"):
		frappe.throw(
			_("Cannot change this complaint in its current status ({0}).").format(st),
			frappe.ValidationError,
		)


@frappe.whitelist()
def submit_complaint(
	business_id: str,
	complaint_title: str,
	complaint_type: str,
	complainant_type: str,
	complainant_name: str,
	complaint_summary: str,
	complaint_details: str,
	requested_remedy: str,
	received_by_user: str,
	complainant_contact_email: str | None = None,
	complainant_contact_phone: str | None = None,
	submission_datetime: str | None = None,
	tender: str | None = None,
	bid_submission: str | None = None,
	evaluation_session: str | None = None,
	award_decision: str | None = None,
	contract: str | None = None,
	supplier: str | None = None,
	exception_record: str | None = None,
	actor_user: str | None = None,
) -> Document:
	"""Create a **Complaint** with required intake fields, **Submitted** + **Admissibility** workflow, **Pending** admissibility.

	Emits **Complaint Status Event** ``Submitted``.
	"""
	bid = norm(business_id)
	if not bid:
		frappe.throw(_("Business ID is required."), frappe.ValidationError)
	ct = norm(complaint_type)
	if ct not in _COMPLAINT_TYPES:
		frappe.throw(
			_("complaint_type must be one of: {0}.").format(", ".join(sorted(_COMPLAINT_TYPES))),
			frappe.ValidationError,
		)
	cpt = norm(complainant_type)
	if cpt not in _COMPLAINANT_TYPES:
		frappe.throw(
			_("complainant_type must be one of: {0}.").format(", ".join(sorted(_COMPLAINANT_TYPES))),
			frappe.ValidationError,
		)
	for label, val in (
		(_("Complaint title"), complaint_title),
		(_("Complainant name"), complainant_name),
		(_("Complaint summary"), complaint_summary),
		(_("Complaint details"), complaint_details),
		(_("Requested remedy"), requested_remedy),
		(_("Received By"), received_by_user),
	):
		if not norm(val):
			frappe.throw(_("{0} is required.").format(label), frappe.ValidationError)

	sub_dt = get_datetime(submission_datetime) if submission_datetime else now_datetime()

	doc = frappe.get_doc(
		{
			"doctype": C,
			"business_id": bid,
			"complaint_title": norm(complaint_title),
			"status": "Submitted",
			"workflow_state": "Admissibility",
			"complaint_type": ct,
			"complaint_stage": "Intake",
			"complainant_type": cpt,
			"complainant_name": norm(complainant_name),
			"complainant_contact_email": norm(complainant_contact_email),
			"complainant_contact_phone": norm(complainant_contact_phone),
			"complaint_summary": norm(complaint_summary),
			"complaint_details": complaint_details,
			"requested_remedy": norm(requested_remedy),
			"submission_datetime": sub_dt,
			"received_by_user": norm(received_by_user),
			"admissibility_status": "Pending",
			"tender": tender or None,
			"bid_submission": bid_submission or None,
			"evaluation_session": evaluation_session or None,
			"award_decision": award_decision or None,
			"contract": contract or None,
			"supplier": supplier or None,
			"exception_record": exception_record or None,
		}
	)
	doc.insert(ignore_permissions=True)
	append_complaint_event(
		doc.name,
		"Submitted",
		_("Complaint submitted for admissibility review."),
		actor_user=actor_user,
	)
	return doc


@frappe.whitelist()
def review_complaint_admissibility(
	complaint: str,
	admissibility: str,
	admissibility_reason: str | None = None,
	reviewed_by_user: str | None = None,
	actor_user: str | None = None,
) -> Document:
	"""Set **admissibility_status** explicitly and transition workflow. Emits **AdmissibilityReviewed**.

	- **Admissible** → **Under Review** / **Panel Review** / **Formal Review**
	- **Inadmissible** → **Closed** (workflow **Closed**)
	- **Deferred** → stays in admissibility queue (reason recommended)
	"""
	doc = get_complaint_doc(complaint)
	ensure_complaint_not_locked(doc)
	_ensure_can_intake_transition(doc)

	out = norm(admissibility)
	if out not in _ADM_OUTCOMES:
		frappe.throw(
			_("admissibility must be one of: {0}.").format(", ".join(sorted(_ADM_OUTCOMES))),
			frappe.ValidationError,
		)

	st = norm(doc.status)
	cur_adm = norm(doc.admissibility_status)
	if cur_adm not in ("Pending", "Deferred"):
		frappe.throw(
			_("Admissibility has already been resolved (current: {0}).").format(cur_adm or "—"),
			frappe.ValidationError,
		)
	if st not in ("Draft", "Submitted"):
		frappe.throw(
			_("Complaint must be Draft or Submitted to review admissibility (current status: {0}).").format(st),
			frappe.ValidationError,
		)

	reason = norm(admissibility_reason)
	if out == "Deferred" and not reason:
		frappe.throw(_("Admissibility reason is required when the outcome is Deferred."), frappe.ValidationError)
	if out == "Inadmissible" and not reason:
		frappe.throw(_("Admissibility reason is required when the outcome is Inadmissible."), frappe.ValidationError)

	reviewer = norm(reviewed_by_user) or frappe.session.user
	if not frappe.db.exists("User", reviewer):
		frappe.throw(_("Reviewed By user not found."), frappe.ValidationError)

	doc.admissibility_status = out
	doc.admissibility_reason = reason or None
	doc.reviewed_by_user = reviewer
	doc.reviewed_on = now_datetime()

	if out == "Admissible":
		doc.status = "Under Review"
		doc.workflow_state = "Panel Review"
		doc.complaint_stage = "Formal Review"
	elif out == "Inadmissible":
		doc.status = "Closed"
		doc.workflow_state = "Closed"
		doc.complaint_stage = "Closed"
		doc.closure_date = today()
	elif out == "Deferred":
		doc.workflow_state = "Admissibility"
		doc.status = "Submitted"

	save_complaint(doc)
	summary = _("Admissibility outcome: {0}.").format(out)
	if reason:
		summary = summary + " " + reason
	append_complaint_event(doc.name, "AdmissibilityReviewed", summary, actor_user=actor_user or reviewer)
	return doc


@frappe.whitelist()
def withdraw_complaint(complaint: str, reason: str | None = None, actor_user: str | None = None) -> Document:
	"""Withdraw a complaint before it is terminal. Emits **Closed** (pack uses **Closed** for lifecycle end)."""
	doc = get_complaint_doc(complaint)
	ensure_complaint_not_locked(doc)
	st = norm(doc.status)
	if st in ("Closed", "Withdrawn", "Decided"):
		frappe.throw(_("Cannot withdraw a complaint in status {0}.").format(st), frappe.ValidationError)

	doc.status = "Withdrawn"
	doc.workflow_state = "Closed"
	doc.complaint_stage = "Closed"
	doc.closure_date = today()
	save_complaint(doc)

	msg = _("Complaint withdrawn.")
	r = norm(reason)
	if r:
		msg = msg + " " + r
	append_complaint_event(doc.name, "Closed", msg, actor_user=actor_user)
	return doc
