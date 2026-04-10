# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""PROC-STORY-112: inspection checklist/parameter results and tolerance evaluation."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt

IR = "Inspection Record"
IMT = "Inspection Method Template"
IPL = "Inspection Parameter Line"
ITR = "Inspection Test Result"

Outcome = str  # Pass | Fail | Inconclusive


def _norm(s: str | None) -> str:
	return (s or "").strip()


def apply_template_fields_to_inspection_document(doc, template_name: str) -> None:
	"""Copy method type and ``requires_*`` flags from **Inspection Method Template** onto an **Inspection Record**."""
	tpl = frappe.get_doc(IMT, _norm(template_name))
	if not tpl.name:
		frappe.throw(_("Inspection Method Template not found."), frappe.ValidationError)
	if hasattr(tpl, "active") and not int(tpl.active or 0):
		frappe.throw(_("Inspection Method Template is not active."), frappe.ValidationError)
	doc.inspection_method_type = _norm(tpl.inspection_method_type) or doc.inspection_method_type
	for fn in (
		"requires_sampling",
		"requires_lab_test",
		"requires_field_measurement",
	):
		if hasattr(doc, fn) and hasattr(tpl, fn):
			setattr(doc, fn, int(getattr(tpl, fn) or 0))
	doc.inspection_method_template = tpl.name


def apply_inspection_template(inspection_record_id: str, template_id: str) -> dict[str, Any]:
	"""Re-apply an **Inspection Method Template** to an existing inspection (PROC-STORY-112)."""
	iname = _norm(inspection_record_id)
	tname = _norm(template_id)
	if not iname or not frappe.db.exists(IR, iname):
		frappe.throw(_("Inspection Record not found."), frappe.ValidationError)
	if not tname or not frappe.db.exists(IMT, tname):
		frappe.throw(_("Inspection Method Template not found."), frappe.ValidationError)
	doc = frappe.get_doc(IR, iname)
	apply_template_fields_to_inspection_document(doc, tname)
	doc.save(ignore_permissions=True)
	return {"name": doc.name}


def evaluate_parameter_tolerance(
	parameter_line_id: str,
	*,
	observed_numeric: float | None = None,
	observed_boolean: bool | None = None,
) -> Outcome:
	"""Evaluate observed values against **Inspection Parameter Line** tolerance rules.

	Returns ``Pass``, ``Fail``, or ``Inconclusive``.

	**Formulas** (``v`` = observed numeric, ``T`` = target, ``tol`` = tolerance value,
	``e_min`` / ``e_max`` = expected min/max):

	- **MinMax:** Fail if ``e_min`` is set and ``v < e_min``; fail if ``e_max`` is set and ``v > e_max``;
	  Pass if in range; Inconclusive if neither bound is set.
	- **Absolute:** Pass iff ``|v - T| <= tol`` (requires ``T`` and ``tol``).
	- **Percent:** Pass iff ``T * (1 - tol/100) <= v <= T * (1 + tol/100)`` (requires ``T`` and ``tol``).
	- **PassFailOnly:** Pass/Fail from ``observed_boolean``; Inconclusive if missing.
	- **None:** Inconclusive (no automatic numeric rule).
	"""
	pl = frappe.get_doc(IPL, parameter_line_id)
	tt = _norm(pl.tolerance_type) or "None"

	if tt == "PassFailOnly":
		if observed_boolean is None:
			return "Inconclusive"
		return "Pass" if observed_boolean else "Fail"

	if tt == "None":
		return "Inconclusive"

	if observed_numeric is None:
		return "Inconclusive"

	v = flt(observed_numeric)
	tgt = pl.target_value
	tol = pl.tolerance_value
	emin = pl.expected_min_value
	emax = pl.expected_max_value

	if tt == "MinMax":
		if emin is not None and v < flt(emin):
			return "Fail"
		if emax is not None and v > flt(emax):
			return "Fail"
		if emin is None and emax is None:
			return "Inconclusive"
		return "Pass"

	if tt == "Absolute":
		if tgt is None or tol is None:
			return "Inconclusive"
		if abs(v - flt(tgt)) <= flt(tol):
			return "Pass"
		return "Fail"

	if tt == "Percent":
		if tgt is None or tol is None:
			return "Inconclusive"
		t = flt(tgt)
		p = flt(tol)
		low = t * (1 - p / 100.0)
		high = t * (1 + p / 100.0)
		if low <= v <= high:
			return "Pass"
		return "Fail"

	return "Inconclusive"


def _outcome_to_pass_fail_select(outcome: Outcome) -> str:
	if outcome == "Pass":
		return "Pass"
	if outcome == "Fail":
		return "Fail"
	return "Pending"


def _outcome_to_parameter_line_status(outcome: Outcome) -> str:
	if outcome == "Pass":
		return "Passed"
	if outcome == "Fail":
		return "Failed"
	return "Pending"


def _latest_test_result_name(inspection_record: str, parameter_line: str) -> str | None:
	rows = frappe.get_all(
		ITR,
		filters={"inspection_record": inspection_record, "inspection_parameter_line": parameter_line},
		pluck="name",
		order_by="modified desc",
		limit=1,
	)
	return rows[0] if rows else None


def record_parameter_result(
	inspection_record_id: str,
	parameter_line_id: str,
	*,
	observed_numeric_value: float | None = None,
	observed_text_value: str | None = None,
	observed_boolean_value: bool | None = None,
	pass_fail_result: str | None = None,
	result_notes: str | None = None,
) -> dict[str, Any]:
	"""Create or update the latest **Inspection Test Result** for a parameter line and sync line status."""
	irn = _norm(inspection_record_id)
	pln = _norm(parameter_line_id)
	if not irn or not frappe.db.exists(IR, irn):
		frappe.throw(_("Inspection Record not found."), frappe.ValidationError)
	if not pln or not frappe.db.exists(IPL, pln):
		frappe.throw(_("Inspection Parameter Line not found."), frappe.ValidationError)
	pl_ir = frappe.db.get_value(IPL, pln, "inspection_record")
	if pl_ir != irn:
		frappe.throw(_("Parameter line does not belong to this inspection."), frappe.ValidationError)

	outcome = None
	pf = _norm(pass_fail_result)
	if pf in ("Pass", "Fail", "Not Applicable", "Pending"):
		final_pf = pf
	else:
		outcome = evaluate_parameter_tolerance(
			pln,
			observed_numeric=observed_numeric_value,
			observed_boolean=observed_boolean_value,
		)
		final_pf = _outcome_to_pass_fail_select(outcome)

	ln = _latest_test_result_name(irn, pln)
	if ln:
		tr = frappe.get_doc(ITR, ln)
	else:
		tr = frappe.new_doc(ITR)
		tr.inspection_record = irn
		tr.inspection_parameter_line = pln

	if observed_numeric_value is not None:
		tr.observed_numeric_value = flt(observed_numeric_value)
	if observed_text_value is not None:
		tr.observed_text_value = observed_text_value
	if observed_boolean_value is not None:
		tr.observed_boolean_value = 1 if observed_boolean_value else 0
	tr.pass_fail_result = final_pf
	if result_notes is not None:
		tr.result_notes = result_notes
	tr.save(ignore_permissions=True)

	pl = frappe.get_doc(IPL, pln)
	if outcome is None:
		if final_pf == "Pass":
			pl.status = "Passed"
		elif final_pf == "Fail":
			pl.status = "Failed"
		elif final_pf == "Not Applicable":
			pl.status = "Waived"
		else:
			pl.status = "Pending"
	else:
		pl.status = _outcome_to_parameter_line_status(outcome)
	pl.save(ignore_permissions=True)

	return {
		"name": tr.name,
		"pass_fail_result": tr.pass_fail_result,
		"tolerance_outcome": outcome or final_pf,
		"parameter_line_status": pl.status,
	}


def record_checklist_result(
	inspection_record_id: str,
	*,
	row_idx: int | None = None,
	check_item_no: int | None = None,
	result_status: str,
	observed_result: str | None = None,
) -> dict[str, Any]:
	"""Update a **Inspection Checklist Line** row on the inspection (match by ``idx`` or ``check_item_no``)."""
	irn = _norm(inspection_record_id)
	if not irn or not frappe.db.exists(IR, irn):
		frappe.throw(_("Inspection Record not found."), frappe.ValidationError)
	if row_idx is None and check_item_no is None:
		frappe.throw(_("Specify row_idx or check_item_no."), frappe.ValidationError)

	doc = frappe.get_doc(IR, irn)
	rows = doc.get("checklist_lines") or []
	target = None
	if row_idx is not None:
		for r in rows:
			if int(r.idx or 0) == int(row_idx):
				target = r
				break
	else:
		for r in rows:
			if int(r.check_item_no or 0) == int(check_item_no or 0):
				target = r
				break
	if target is None:
		frappe.throw(_("Checklist line not found."), frappe.ValidationError)

	target.result_status = _norm(result_status) or "Pending"
	if observed_result is not None:
		target.observed_result = observed_result
	doc.save(ignore_permissions=True)
	return {"inspection_record": doc.name, "row_idx": target.idx}


def recompute_inspection_result(inspection_record_id: str) -> dict[str, Any]:
	"""Recompute parameter and checklist summary counts and roll up **inspection_result**."""
	irn = _norm(inspection_record_id)
	if not irn or not frappe.db.exists(IR, irn):
		frappe.throw(_("Inspection Record not found."), frappe.ValidationError)

	doc = frappe.get_doc(IR, irn)

	# Checklist
	cl = doc.get("checklist_lines") or []
	doc.checklist_items_count = len(cl)
	cl_fail = sum(1 for r in cl if _norm(r.result_status) == "Fail")
	cl_pending = sum(1 for r in cl if _norm(r.result_status) in ("", "Pending"))

	# Parameters: all lines for this inspection
	pl_names = frappe.get_all(IPL, filters={"inspection_record": irn}, pluck="name") or []
	doc.parameter_tests_count = len(pl_names)
	passed = 0
	failed = 0
	pending = 0
	for pln in pl_names:
		latest = _latest_test_result_name(irn, pln)
		if not latest:
			pending += 1
			continue
		pf = _norm(frappe.db.get_value(ITR, latest, "pass_fail_result"))
		if pf == "Pass":
			passed += 1
		elif pf == "Fail":
			failed += 1
		elif pf == "Not Applicable":
			pass
		else:
			pending += 1

	doc.parameter_tests_passed_count = passed
	doc.parameter_tests_failed_count = failed

	# Roll-up (explicit; acceptance is out of scope here)
	if cl_fail > 0 or failed > 0:
		doc.inspection_result = "Fail"
	elif pending > 0 or cl_pending > 0:
		doc.inspection_result = "Pending"
	elif len(pl_names) == 0 and len(cl) == 0:
		doc.inspection_result = doc.inspection_result or "Pending"
	else:
		doc.inspection_result = "Pass"

	doc.save(ignore_permissions=True)
	return {
		"name": doc.name,
		"inspection_result": doc.inspection_result,
		"parameter_tests_passed_count": doc.parameter_tests_passed_count,
		"parameter_tests_failed_count": doc.parameter_tests_failed_count,
		"parameter_tests_count": doc.parameter_tests_count,
		"checklist_items_count": doc.checklist_items_count,
	}
