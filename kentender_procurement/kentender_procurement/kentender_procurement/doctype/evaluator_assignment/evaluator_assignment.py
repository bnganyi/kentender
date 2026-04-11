# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Evaluator Assignment — committee seat on an evaluation session (PROC-STORY-059)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.permissions.registry import MATRIX_ROLE
from kentender.utils.display_label import code_title_label

EVALUATION_SESSION = "Evaluation Session"
DOCTYPE = "Evaluator Assignment"

_STATUS_WITHDRAWN = "Withdrawn"
_STATUS_REPLACED = "Replaced"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class EvaluatorAssignment(Document):
	def validate(self):
		self._normalize_text()
		self._validate_evaluation_session()
		self._validate_separation_of_duties()
		self._validate_unique_evaluator_per_session()
		self._validate_status_and_replacement()
		self._set_display_label()

	def _normalize_text(self) -> None:
		if self.notes and isinstance(self.notes, str):
			self.notes = self.notes.strip()

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

	def _validate_separation_of_duties(self) -> None:
		"""Matrix §16 — Evaluator cannot be Supplier or Contract Manager."""
		eu = _strip(self.evaluator_user)
		if not eu:
			return
		roles = set(frappe.get_roles(eu))
		if MATRIX_ROLE.SUPPLIER.value in roles:
			frappe.throw(
				_("A user with the Supplier role cannot be assigned as an Evaluator."),
				frappe.ValidationError,
				title=_("Separation of duties"),
			)
		if MATRIX_ROLE.CONTRACT_MANAGER.value in roles:
			frappe.throw(
				_("A user with the Contract Manager role cannot be assigned as an Evaluator."),
				frappe.ValidationError,
				title=_("Separation of duties"),
			)

	def _validate_unique_evaluator_per_session(self) -> None:
		es = _strip(self.evaluation_session)
		eu = _strip(self.evaluator_user)
		if not es or not eu:
			return
		filters: dict = {"evaluation_session": es, "evaluator_user": eu}
		if _strip(self.name):
			filters["name"] = ("!=", self.name)
		others = frappe.get_all(DOCTYPE, filters=filters, pluck="name", limit=1)
		if others:
			frappe.throw(
				_("This user is already assigned to this evaluation session."),
				frappe.ValidationError,
				title=_("Duplicate assignment"),
			)

	def _validate_status_and_replacement(self) -> None:
		st = _strip(self.assignment_status)
		if st in (_STATUS_WITHDRAWN, _STATUS_REPLACED) and not self.withdrawn_on:
			frappe.throw(
				_("Withdrawn On is required when assignment status is {0}.").format(frappe.bold(st)),
				frappe.ValidationError,
				title=_("Missing withdrawal date"),
			)
		if st == _STATUS_REPLACED:
			ru = _strip(self.replacement_user)
			if not ru:
				frappe.throw(
					_("Replacement User is required when assignment status is Replaced."),
					frappe.ValidationError,
					title=_("Missing replacement"),
				)
			eu = _strip(self.evaluator_user)
			if ru == eu:
				frappe.throw(
					_("Replacement User must differ from the assigned user."),
					frappe.ValidationError,
					title=_("Invalid replacement"),
				)

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.evaluator_user), _strip(self.committee_role) or "—")
