# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Evaluation Approval Submission Record — append-only audit for evaluation report workflow (PROC-STORY-066).

Pack title uses a slash; Frappe DocType name is **Evaluation Approval Submission Record** (no `/`).
Services in PROC-STORY-071 are expected to insert rows (often with ignore_permissions).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

EVALUATION_SESSION = "Evaluation Session"
EVALUATION_REPORT = "Evaluation Report"
USER = "User"
ROLE = "Role"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class EvaluationApprovalSubmissionRecord(Document):
	def validate(self):
		if not self.is_new():
			frappe.throw(
				_("Evaluation Approval Submission Record cannot be modified."),
				frappe.ValidationError,
				title=_("Append-only record"),
			)
		if self.comments and isinstance(self.comments, str):
			self.comments = self.comments.strip()
		self._validate_evaluation_session()
		self._validate_evaluation_report()
		self._validate_actor_user()
		self._validate_actor_role()
		self._set_display_label()

	def _validate_evaluation_session(self) -> None:
		sn = _strip(self.evaluation_session)
		if not sn:
			return
		if not frappe.db.exists(EVALUATION_SESSION, sn):
			frappe.throw(
				_("Evaluation Session {0} does not exist.").format(frappe.bold(sn)),
				frappe.ValidationError,
				title=_("Invalid evaluation session"),
			)

	def _validate_evaluation_report(self) -> None:
		rn = _strip(self.evaluation_report)
		es = _strip(self.evaluation_session)
		if not rn:
			return
		if not frappe.db.exists(EVALUATION_REPORT, rn):
			frappe.throw(
				_("Evaluation Report {0} does not exist.").format(frappe.bold(rn)),
				frappe.ValidationError,
				title=_("Invalid evaluation report"),
			)
		report_session = frappe.db.get_value(EVALUATION_REPORT, rn, "evaluation_session")
		if es and report_session and _strip(report_session) != es:
			frappe.throw(
				_("Evaluation Report must belong to the selected Evaluation Session."),
				frappe.ValidationError,
				title=_("Report session mismatch"),
			)
		session_tender = frappe.db.get_value(EVALUATION_SESSION, es, "tender") if es else None
		report_tender = frappe.db.get_value(EVALUATION_REPORT, rn, "tender")
		if session_tender and report_tender and _strip(session_tender) != _strip(report_tender):
			frappe.throw(
				_("Evaluation Report tender must match the Evaluation Session tender."),
				frappe.ValidationError,
				title=_("Report tender mismatch"),
			)

	def _validate_actor_user(self) -> None:
		un = _strip(self.actor_user)
		if not un:
			return
		if not frappe.db.exists(USER, un):
			frappe.throw(
				_("User {0} does not exist.").format(frappe.bold(un)),
				frappe.ValidationError,
				title=_("Invalid actor user"),
			)

	def _validate_actor_role(self) -> None:
		rn = _strip(self.actor_role)
		if not rn:
			return
		if not frappe.db.exists(ROLE, rn):
			frappe.throw(
				_("Role {0} does not exist.").format(frappe.bold(rn)),
				frappe.ValidationError,
				title=_("Invalid actor role"),
			)

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.action_type) or "—", _strip(self.evaluation_session) or "—")

	def on_trash(self):
		frappe.throw(
			_("Evaluation Approval Submission Record cannot be deleted."),
			frappe.ValidationError,
			title=_("Append-only record"),
		)
