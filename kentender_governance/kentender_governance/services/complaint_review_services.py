# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""GOV-STORY-023: panel assignment, review submission, and complaint decision issuance + status events."""

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
CRPA = "Complaint Review Panel Assignment"
CRR = "Complaint Review Record"
CD = "Complaint Decision"

_ROLE_TYPES = frozenset({"Chair", "Member", "Secretary", "Observer"})
_DECISION_RESULTS = frozenset({"Upheld", "Partially Upheld", "Rejected", "Dismissed", "Remedy Ordered"})


def _require_admissible_for_review(doc: Document) -> None:
	if norm(doc.admissibility_status) != "Admissible":
		frappe.throw(
			_("Full review requires admissibility **Admissible** (current: {0}).").format(
				norm(doc.admissibility_status) or "—"
			),
			frappe.ValidationError,
		)


def _require_in_panel_review_phase(doc: Document) -> None:
	st = norm(doc.status)
	wf = norm(doc.workflow_state)
	if st != "Under Review" or wf != "Panel Review":
		frappe.throw(
			_("Assignment requires **Under Review** and **Panel Review** (current: {0} / {1}).").format(st, wf),
			frappe.ValidationError,
		)


def _has_active_panel_assignment(complaint: str, user: str) -> bool:
	return bool(
		frappe.db.exists(
			CRPA,
			{
				"complaint": complaint,
				"user": user,
				"assignment_status": "Active",
			},
		)
	)


@frappe.whitelist()
def assign_complaint_reviewer(
	complaint: str,
	user: str,
	role_type: str = "Member",
	assignment_status: str = "Active",
	notes: str | None = None,
	actor_user: str | None = None,
) -> Document:
	"""Create **Complaint Review Panel Assignment**. Requires admissibility resolved and **Panel Review** phase."""
	doc = get_complaint_doc(complaint)
	ensure_complaint_not_locked(doc)
	_require_admissible_for_review(doc)
	_require_in_panel_review_phase(doc)

	rt = norm(role_type) or "Member"
	if rt not in _ROLE_TYPES:
		frappe.throw(_("role_type must be one of: {0}.").format(", ".join(sorted(_ROLE_TYPES))), frappe.ValidationError)
	u = norm(user)
	if not u or not frappe.db.exists("User", u):
		frappe.throw(_("Reviewer user not found."), frappe.ValidationError)

	p = frappe.get_doc(
		{
			"doctype": CRPA,
			"complaint": doc.name,
			"user": u,
			"role_type": rt,
			"assignment_status": norm(assignment_status) or "Active",
			"assigned_on": now_datetime(),
			"notes": notes,
		}
	)
	p.insert(ignore_permissions=True)
	append_complaint_event(
		doc.name,
		"PanelAssigned",
		_("Panel member assigned: {0} ({1}).").format(u, rt),
		actor_user=actor_user,
	)
	return p


@frappe.whitelist()
def submit_complaint_review(
	complaint: str,
	review_summary: str,
	recommended_outcome: str,
	reviewer_user: str | None = None,
	analysis_notes: str | None = None,
	actor_user: str | None = None,
) -> Document:
	"""Create **Complaint Review Record** (**Submitted**). Reviewer must have an **Active** panel assignment."""
	doc = get_complaint_doc(complaint)
	ensure_complaint_not_locked(doc)
	_require_admissible_for_review(doc)
	if norm(doc.workflow_state) != "Panel Review":
		frappe.throw(_("Review submission requires workflow **Panel Review**."), frappe.ValidationError)

	rev = norm(reviewer_user) or frappe.session.user
	if not frappe.db.exists("User", rev):
		frappe.throw(_("Reviewer user not found."), frappe.ValidationError)
	if not _has_active_panel_assignment(doc.name, rev):
		frappe.throw(_("Reviewer must have an active panel assignment for this complaint."), frappe.ValidationError)

	if not norm(review_summary) or not norm(recommended_outcome):
		frappe.throw(_("Review summary and recommended outcome are required."), frappe.ValidationError)

	rec = frappe.get_doc(
		{
			"doctype": CRR,
			"complaint": doc.name,
			"reviewer_user": rev,
			"review_summary": norm(review_summary),
			"recommended_outcome": norm(recommended_outcome),
			"analysis_notes": analysis_notes,
			"submitted_on": now_datetime(),
			"status": "Submitted",
		}
	)
	rec.insert(ignore_permissions=True)
	append_complaint_event(
		doc.name,
		"ReviewSubmitted",
		_("Review submitted by {0}.").format(rev),
		actor_user=actor_user or rev,
	)
	return rec


@frappe.whitelist()
def issue_complaint_decision(
	complaint: str,
	decision_business_id: str,
	decision_result: str,
	decision_summary: str,
	decided_by_user: str,
	decision_datetime: str | None = None,
	detailed_reasoning: str | None = None,
	actor_user: str | None = None,
) -> Document:
	"""Issue **Complaint Decision** (**Final**) after at least one **Submitted** review record exists."""
	doc = get_complaint_doc(complaint)
	ensure_complaint_not_locked(doc)
	_require_admissible_for_review(doc)
	if norm(doc.workflow_state) != "Panel Review":
		frappe.throw(_("Issuing a decision requires workflow **Panel Review**."), frappe.ValidationError)

	if not frappe.db.exists(
		CRR,
		{"complaint": doc.name, "status": "Submitted"},
	):
		frappe.throw(_("At least one submitted Complaint Review Record is required."), frappe.ValidationError)

	bid = norm(decision_business_id)
	if not bid:
		frappe.throw(_("Decision business_id is required."), frappe.ValidationError)
	dr = norm(decision_result)
	if dr not in _DECISION_RESULTS:
		frappe.throw(
			_("decision_result must be one of: {0}.").format(", ".join(sorted(_DECISION_RESULTS))),
			frappe.ValidationError,
		)
	decider = norm(decided_by_user)
	if not decider or not frappe.db.exists("User", decider):
		frappe.throw(_("Decided By user not found."), frappe.ValidationError)
	if not norm(decision_summary):
		frappe.throw(_("Decision summary is required."), frappe.ValidationError)

	dt = get_datetime(decision_datetime) if decision_datetime else now_datetime()

	d = frappe.get_doc(
		{
			"doctype": CD,
			"business_id": bid,
			"complaint": doc.name,
			"status": "Final",
			"decision_datetime": dt,
			"decided_by_user": decider,
			"decision_result": dr,
			"decision_summary": norm(decision_summary),
			"detailed_reasoning": detailed_reasoning,
		}
	)
	d.insert(ignore_permissions=True)

	doc.status = "Decided"
	doc.workflow_state = "Decision"
	doc.actual_decision_date = today()
	save_complaint(doc)

	append_complaint_event(
		doc.name,
		"Decided",
		_("Complaint decision issued: {0}.").format(dr),
		actor_user=actor_user or decider,
	)
	return d
