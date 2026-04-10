# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Evaluation Score Line — criterion score under an Evaluation Record (PROC-STORY-062).

Table rows are validated from Evaluation Record.validate(); Frappe does not run child
Document.validate() on parent insert.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import frappe
from frappe import _
from frappe.model.document import Document

if TYPE_CHECKING:
	from frappe.model.document import Document as DocumentT

EVALUATION_SESSION = "Evaluation Session"
TENDER_CRITERIA = "Tender Criteria"

SCORE_NUMERIC = "Numeric"
SCORE_PASS_FAIL = "Pass/Fail"


def _strip(s: str | None) -> str:
	return (s or "").strip()


def _float_match(a: object, b: object) -> bool:
	if a is None and b is None:
		return True
	if a is None or b is None:
		return False
	try:
		return abs(float(a) - float(b)) < 1e-9
	except (TypeError, ValueError):
		return False


def validate_evaluation_score_line_row(parent: "DocumentT", line: "DocumentT") -> None:
	"""Validate one score line against an in-memory Evaluation Record (parent may be unsaved)."""
	_normalize_score_line_text(line)
	_validate_formula_json_line(line)
	session_tender = _session_tender_from_parent(parent)
	tc_row = _tender_criteria_row_for_line(line)
	_validate_tender_alignment_line(session_tender, tc_row)
	_validate_denormalized_fields_line(line, tc_row)
	st = _strip(tc_row.get("score_type"))
	if st == SCORE_NUMERIC:
		_validate_numeric_scoring_line(line, tc_row)
	elif st == SCORE_PASS_FAIL:
		_validate_pass_fail_scoring_line(line)
	_set_weighted_score_line(line, st)


def _normalize_score_line_text(line: "DocumentT") -> None:
	if line.comments and isinstance(line.comments, str):
		line.comments = line.comments.strip()
	if line.formula_result_json and isinstance(line.formula_result_json, str):
		line.formula_result_json = line.formula_result_json.strip()


def _validate_formula_json_line(line: "DocumentT") -> None:
	raw = line.formula_result_json
	if not raw or not isinstance(raw, str):
		return
	try:
		json.loads(raw)
	except json.JSONDecodeError:
		frappe.throw(
			_("Formula Result JSON must be valid JSON."),
			frappe.ValidationError,
			title=_("Invalid JSON"),
		)


def _session_tender_from_parent(parent: "DocumentT") -> str:
	es = _strip(getattr(parent, "evaluation_session", None))
	if not es:
		frappe.throw(
			_("Parent Evaluation Record must have an Evaluation Session."),
			frappe.ValidationError,
			title=_("Missing session"),
		)
	if not frappe.db.exists(EVALUATION_SESSION, es):
		frappe.throw(
			_("Evaluation Session {0} does not exist.").format(frappe.bold(es)),
			frappe.ValidationError,
			title=_("Invalid evaluation session"),
		)
	tn = frappe.db.get_value(EVALUATION_SESSION, es, "tender")
	return _strip(tn)


def _tender_criteria_row_for_line(line: "DocumentT") -> dict:
	cn = _strip(line.tender_criteria)
	if not cn:
		return {}
	if not frappe.db.exists(TENDER_CRITERIA, cn):
		frappe.throw(
			_("Tender Criteria {0} does not exist.").format(frappe.bold(cn)),
			frappe.ValidationError,
			title=_("Invalid tender criteria"),
		)
	return frappe.db.get_value(
		TENDER_CRITERIA,
		cn,
		["tender", "criteria_type", "criteria_title", "score_type", "max_score", "weight_percentage"],
		as_dict=True,
	)


def _validate_tender_alignment_line(session_tender: str, tc_row: dict) -> None:
	tc_tender = _strip(tc_row.get("tender"))
	if session_tender and tc_tender and session_tender != tc_tender:
		frappe.throw(
			_("Tender Criteria must belong to the same Tender as the Evaluation Session."),
			frappe.ValidationError,
			title=_("Criteria tender mismatch"),
		)


def _validate_denormalized_fields_line(line: "DocumentT", tc_row: dict) -> None:
	if _strip(line.criteria_type) != _strip(tc_row.get("criteria_type")):
		frappe.throw(
			_("Criteria Type must match the linked Tender Criteria."),
			frappe.ValidationError,
			title=_("Criteria type mismatch"),
		)
	if _strip(line.criteria_title) != _strip(tc_row.get("criteria_title")):
		frappe.throw(
			_("Criteria Title must match the linked Tender Criteria."),
			frappe.ValidationError,
			title=_("Criteria title mismatch"),
		)
	if not _float_match(line.max_score, tc_row.get("max_score")):
		frappe.throw(
			_("Max Score must match the linked Tender Criteria."),
			frappe.ValidationError,
			title=_("Max score mismatch"),
		)
	if not _float_match(line.weight_percentage, tc_row.get("weight_percentage")):
		frappe.throw(
			_("Weight Percentage must match the linked Tender Criteria."),
			frappe.ValidationError,
			title=_("Weight mismatch"),
		)


def _validate_numeric_scoring_line(line: "DocumentT", tc_row: dict) -> None:
	pf = _strip(line.pass_fail_result)
	if pf in ("Pass", "Fail"):
		frappe.throw(
			_("Pass / Fail Result must be Pending or Not Applicable for numeric criteria."),
			frappe.ValidationError,
			title=_("Invalid pass/fail for numeric"),
		)
	if line.score_value is None:
		frappe.throw(
			_("Score Value is required for numeric criteria."),
			frappe.ValidationError,
			title=_("Missing score"),
		)
	tc_max = float(tc_row.get("max_score") or 0)
	if tc_max <= 0:
		frappe.throw(
			_("Linked Tender Criteria has an invalid Max Score for numeric scoring."),
			frappe.ValidationError,
			title=_("Invalid max score"),
		)
	sv = float(line.score_value)
	if sv < 0 or sv > tc_max:
		frappe.throw(
			_("Score Value must be between 0 and {0}.").format(frappe.bold(str(tc_max))),
			frappe.ValidationError,
			title=_("Score out of range"),
		)


def _validate_pass_fail_scoring_line(line: "DocumentT") -> None:
	sv = line.score_value
	if sv is not None:
		try:
			fv = float(sv)
		except (TypeError, ValueError):
			frappe.throw(
				_("Score Value must be numeric for pass/fail criteria."),
				frappe.ValidationError,
				title=_("Invalid score value"),
			)
		if fv < 0 or fv > 1:
			frappe.throw(
				_("Score Value for pass/fail criteria must be between 0 and 1."),
				frappe.ValidationError,
				title=_("Score out of range"),
			)


def _set_weighted_score_line(line: "DocumentT", score_type: str) -> None:
	if score_type == SCORE_NUMERIC:
		sv = float(line.score_value or 0)
		wp = float(line.weight_percentage or 0)
		line.weighted_score = sv * wp / 100.0
	else:
		line.weighted_score = 0.0


class EvaluationScoreLine(Document):
	def validate(self):
		if self.parent and frappe.db.exists(self.parenttype, self.parent):
			parent = frappe.get_doc(self.parenttype, self.parent)
			validate_evaluation_score_line_row(parent, self)
