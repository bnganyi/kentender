# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Evaluation aggregation and ranking (PROC-STORY-070).

Writes **Evaluation Aggregation Result** rows via :func:`frappe.flags.in_evaluation_aggregation_service`.
First-pass formulas:

- **Technical / financial:** mean of ``total_stage_score`` on **Locked** ``Evaluation Record`` rows for
  that bid, scoped to scoring stages whose ``stage_type`` is Technical or Financial Evaluation.
- **Combined:** ``technical_weight * technical_score_average + financial_weight * financial_score`` when
  both exist; otherwise the available component.
- **Ranking:** descending ``combined_score`` among non-disqualified bids; disqualified bids get
  ``overall_result`` = Not Ranked.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

ER = "Evaluation Record"
EAR = "Evaluation Aggregation Result"
EST = "Evaluation Stage"
ES = "Evaluation Session"
EDR = "Evaluation Disqualification Record"

_STAGE_TECH = "Technical Evaluation"
_STAGE_FIN = "Financial Evaluation"

_STATUS_LOCKED = "Locked"
_EDR_CONFIRMED = "Confirmed"
_CALC_COMPLETE = "Complete"
_CALC_STALE = "Stale"

_PRELIM_DISQ = "Disqualified"
_PRELIM_RESP = "Responsive"
_OVERALL_NOT_RANKED = "Not Ranked"
_OVERALL_PASS = "Pass"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _agg_save(doc) -> None:
	prev = getattr(frappe.flags, "in_evaluation_aggregation_service", False)
	frappe.flags.in_evaluation_aggregation_service = True
	try:
		doc.save(ignore_permissions=True)
	finally:
		frappe.flags.in_evaluation_aggregation_service = prev


def _agg_insert(doc) -> None:
	prev = getattr(frappe.flags, "in_evaluation_aggregation_service", False)
	frappe.flags.in_evaluation_aggregation_service = True
	try:
		doc.insert(ignore_permissions=True)
	finally:
		frappe.flags.in_evaluation_aggregation_service = prev


def _scoring_stage_names(evaluation_session: str, stage_type: str) -> list[str]:
	return (
		frappe.get_all(
			EST,
			filters={
				"evaluation_session": evaluation_session,
				"stage_type": stage_type,
				"is_scoring_stage": 1,
			},
			pluck="name",
		)
		or []
	)


def _locked_record_totals(evaluation_session: str, bid_submission: str, stage_names: list[str]) -> list[float]:
	if not stage_names:
		return []
	rows = (
		frappe.get_all(
			ER,
			filters={
				"evaluation_session": evaluation_session,
				"bid_submission": bid_submission,
				"evaluation_stage": ("in", list(stage_names)),
				"status": _STATUS_LOCKED,
			},
			pluck="total_stage_score",
		)
		or []
	)
	out: list[float] = []
	for v in rows:
		if v is None:
			continue
		try:
			out.append(float(v))
		except (TypeError, ValueError):
			continue
	return out


def _mean(vals: list[float]) -> float | None:
	if not vals:
		return None
	return sum(vals) / float(len(vals))


def _sum_vals(vals: list[float]) -> float | None:
	if not vals:
		return None
	return float(sum(vals))


def _distinct_bids_from_locked_records(evaluation_session: str) -> list[tuple[str, str]]:
	rows = frappe.db.sql(
		"""
		SELECT DISTINCT er.bid_submission, er.supplier
		FROM `tabEvaluation Record` er
		WHERE er.evaluation_session = %s AND er.status = %s
		""",
		(evaluation_session, _STATUS_LOCKED),
		as_dict=True,
	)
	out: list[tuple[str, str]] = []
	for r in rows or []:
		bn = _norm(r.get("bid_submission"))
		sup = _norm(r.get("supplier"))
		if bn and sup:
			out.append((bn, sup))
	return out


def _bid_disqualified(evaluation_session: str, bid_submission: str) -> bool:
	return bool(
		frappe.db.exists(
			EDR,
			{
				"evaluation_session": evaluation_session,
				"bid_submission": bid_submission,
				"status": _EDR_CONFIRMED,
			},
		)
	)


def _get_or_create_ear(evaluation_session: str, bid_submission: str, supplier: str):
	rows = frappe.get_all(
		EAR,
		filters={"evaluation_session": evaluation_session, "bid_submission": bid_submission},
		pluck="name",
		limit=1,
	)
	if rows:
		return frappe.get_doc(EAR, rows[0])
	doc = frappe.get_doc(
		{
			"doctype": EAR,
			"evaluation_session": evaluation_session,
			"bid_submission": bid_submission,
			"supplier": supplier,
			"preliminary_result": "Pending",
			"overall_result": "Pending",
			"calculation_status": _CALC_STALE,
		}
	)
	_agg_insert(doc)
	return doc


def _ensure_ear_rows(evaluation_session: str) -> int:
	"""Create missing aggregation rows for each bid that has at least one locked evaluation record."""
	n = 0
	for bid, sup in _distinct_bids_from_locked_records(evaluation_session):
		rows = frappe.get_all(
			EAR,
			filters={"evaluation_session": evaluation_session, "bid_submission": bid},
			pluck="name",
			limit=1,
		)
		if not rows:
			_get_or_create_ear(evaluation_session, bid, sup)
			n += 1
	return n


def aggregate_technical_scores(evaluation_session_id: str) -> dict[str, Any]:
	"""Recompute technical totals and averages on aggregation rows for the session."""
	sn = _norm(evaluation_session_id)
	if not sn or not frappe.db.exists(ES, sn):
		frappe.throw(_("Evaluation Session not found."), frappe.ValidationError, title=_("Invalid session"))

	_ensure_ear_rows(sn)
	tech_stages = _scoring_stage_names(sn, _STAGE_TECH)
	updated = 0
	for doc in frappe.get_all(EAR, filters={"evaluation_session": sn}, pluck="name"):
		d = frappe.get_doc(EAR, doc)
		totals = _locked_record_totals(sn, d.bid_submission, tech_stages)
		if totals:
			d.technical_score_total = _sum_vals(totals)
			d.technical_score_average = _mean(totals)
		else:
			d.technical_score_total = None
			d.technical_score_average = None
		d.calculation_status = _CALC_STALE
		_agg_save(d)
		updated += 1
	return {"evaluation_session": sn, "rows_updated": updated}


def calculate_financial_score(evaluation_session_id: str) -> dict[str, Any]:
	"""Recompute financial_score on aggregation rows from locked financial-stage records."""
	sn = _norm(evaluation_session_id)
	if not sn or not frappe.db.exists(ES, sn):
		frappe.throw(_("Evaluation Session not found."), frappe.ValidationError, title=_("Invalid session"))

	_ensure_ear_rows(sn)
	fin_stages = _scoring_stage_names(sn, _STAGE_FIN)
	updated = 0
	for doc in frappe.get_all(EAR, filters={"evaluation_session": sn}, pluck="name"):
		d = frappe.get_doc(EAR, doc)
		totals = _locked_record_totals(sn, d.bid_submission, fin_stages)
		d.financial_score = _mean(totals) if totals else None
		d.calculation_status = _CALC_STALE
		_agg_save(d)
		updated += 1
	return {"evaluation_session": sn, "rows_updated": updated}


def _combined_score(tech_avg: float | None, fin_avg: float | None, tw: float, fw: float) -> float | None:
	if tech_avg is not None and fin_avg is not None:
		return float(tw) * tech_avg + float(fw) * fin_avg
	if tech_avg is not None:
		return tech_avg
	if fin_avg is not None:
		return fin_avg
	return None


def calculate_final_ranking(evaluation_session_id: str) -> dict[str, Any]:
	"""Assign ranking_position by combined_score (descending), excluding disqualified bids."""
	sn = _norm(evaluation_session_id)
	if not sn or not frappe.db.exists(ES, sn):
		frappe.throw(_("Evaluation Session not found."), frappe.ValidationError, title=_("Invalid session"))

	names = frappe.get_all(EAR, filters={"evaluation_session": sn}, pluck="name") or []
	ranked: list[tuple[str, float]] = []
	for name in names:
		d = frappe.get_doc(EAR, name)
		if _norm(d.preliminary_result) == _PRELIM_DISQ:
			continue
		cs = d.combined_score
		if cs is None:
			continue
		try:
			ranked.append((name, float(cs)))
		except (TypeError, ValueError):
			continue

	ranked.sort(key=lambda x: x[1], reverse=True)
	ranked_names: set[str] = set()
	for pos, (name, _score) in enumerate(ranked, start=1):
		d = frappe.get_doc(EAR, name)
		d.ranking_position = pos
		d.overall_result = _OVERALL_PASS
		_agg_save(d)
		ranked_names.add(name)

	for name in names:
		if name in ranked_names:
			continue
		d = frappe.get_doc(EAR, name)
		d.ranking_position = 0
		d.overall_result = _OVERALL_NOT_RANKED
		_agg_save(d)

	return {"evaluation_session": sn, "ranked_bids": len(ranked)}


def aggregate_evaluation_results(
	evaluation_session_id: str,
	*,
	technical_weight: float = 0.7,
	financial_weight: float = 0.3,
) -> dict[str, Any]:
	"""Run technical aggregation, financial scores, combined score, disqualification flags, ranking, Complete."""
	sn = _norm(evaluation_session_id)
	if not sn or not frappe.db.exists(ES, sn):
		frappe.throw(_("Evaluation Session not found."), frappe.ValidationError, title=_("Invalid session"))

	tw = float(technical_weight)
	fw = float(financial_weight)
	if tw < 0 or fw < 0 or (tw + fw) <= 0:
		frappe.throw(_("Weights must be non-negative and sum to a positive value."), frappe.ValidationError)

	aggregate_technical_scores(sn)
	calculate_financial_score(sn)

	for name in frappe.get_all(EAR, filters={"evaluation_session": sn}, pluck="name") or []:
		d = frappe.get_doc(EAR, name)
		if _bid_disqualified(sn, d.bid_submission):
			d.preliminary_result = _PRELIM_DISQ
			d.combined_score = None
		else:
			d.preliminary_result = _PRELIM_RESP
			ta = d.technical_score_average
			fa = d.financial_score
			ta_f = float(ta) if ta is not None else None
			fa_f = float(fa) if fa is not None else None
			d.combined_score = _combined_score(ta_f, fa_f, tw, fw)
		_agg_save(d)

	calculate_final_ranking(sn)

	for name in frappe.get_all(EAR, filters={"evaluation_session": sn}, pluck="name") or []:
		d = frappe.get_doc(EAR, name)
		d.calculation_status = _CALC_COMPLETE
		_agg_save(d)

	return {
		"evaluation_session": sn,
		"aggregation_rows": len(frappe.get_all(EAR, filters={"evaluation_session": sn}, pluck="name") or []),
		"status": _CALC_COMPLETE,
	}
