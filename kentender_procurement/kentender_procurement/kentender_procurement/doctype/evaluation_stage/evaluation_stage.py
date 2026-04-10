# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Evaluation Stage — ordered stage under an evaluation session (PROC-STORY-058)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime

from kentender.utils.display_label import code_title_label

EVALUATION_SESSION = "Evaluation Session"
DOCTYPE = "Evaluation Stage"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class EvaluationStage(Document):
	def validate(self):
		self._normalize_text()
		self._validate_evaluation_session()
		self._validate_stage_order()
		self._validate_datetimes()
		self._validate_minimum_pass_mark()
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

	def _validate_stage_order(self) -> None:
		n = self.stage_order
		if n is None:
			return
		try:
			iv = int(n)
		except (TypeError, ValueError):
			frappe.throw(
				_("Stage Order must be a positive integer."),
				frappe.ValidationError,
				title=_("Invalid stage order"),
			)
		if iv < 1:
			frappe.throw(
				_("Stage Order must be a positive integer."),
				frappe.ValidationError,
				title=_("Invalid stage order"),
			)
		self.stage_order = iv

		es = _strip(self.evaluation_session)
		if not es:
			return
		filters: dict = {"evaluation_session": es, "stage_order": iv}
		if _strip(self.name):
			filters["name"] = ("!=", self.name)
		others = frappe.get_all(DOCTYPE, filters=filters, pluck="name", limit=1)
		if others:
			frappe.throw(
				_("Stage Order {0} already exists for this evaluation session.").format(frappe.bold(str(iv))),
				frappe.ValidationError,
				title=_("Duplicate stage order"),
			)

	def _validate_datetimes(self) -> None:
		started = self.started_on
		completed = self.completed_on
		if not started or not completed:
			return
		ds = get_datetime(started)
		dc = get_datetime(completed)
		if dc < ds:
			frappe.throw(
				_("Completed On cannot be before Started On."),
				frappe.ValidationError,
				title=_("Invalid dates"),
			)

	def _validate_minimum_pass_mark(self) -> None:
		v = self.minimum_pass_mark
		if v is None:
			return
		try:
			fv = float(v)
		except (TypeError, ValueError):
			frappe.throw(
				_("Minimum Pass Mark must be a number."),
				frappe.ValidationError,
				title=_("Invalid pass mark"),
			)
		if fv < 0 or fv > 100:
			frappe.throw(
				_("Minimum Pass Mark must be between 0 and 100."),
				frappe.ValidationError,
				title=_("Invalid pass mark"),
			)

	def _set_display_label(self) -> None:
		n = self.stage_order
		order_part = str(int(n)) if n is not None else ""
		self.display_label = code_title_label(order_part, _strip(self.stage_type) or "—")
