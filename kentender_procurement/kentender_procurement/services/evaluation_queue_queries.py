# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Read-side helpers for evaluation desk queues and script reports (PROC-STORY-072)."""

from __future__ import annotations

from typing import Any

import frappe

EA = "Evaluator Assignment"
COI = "Conflict of Interest Declaration"
ES = "Evaluation Session"
ERPT = "Evaluation Report"
EDR = "Evaluation Disqualification Record"
EAR = "Evaluation Aggregation Result"
TENDER = "Tender"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _session_names_for_entity(procuring_entity: str | None) -> list[str] | None:
	ent = _norm(procuring_entity)
	if not ent:
		return None
	tns = frappe.get_all(TENDER, filters={"procuring_entity": ent}, pluck="name") or []
	if not tns:
		return []
	return frappe.get_all(ES, filters={"tender": ("in", tns)}, pluck="name") or []


def get_my_assigned_evaluations(
	evaluator_user: str | None = None,
	procuring_entity: str | None = None,
) -> list[dict[str, Any]]:
	u = _norm(evaluator_user) or _norm(frappe.session.user)
	if not u:
		return []
	filters: dict[str, Any] = {"evaluator_user": u, "assignment_status": "Active"}
	sn = _session_names_for_entity(procuring_entity)
	if sn is not None:
		if not sn:
			return []
		filters["evaluation_session"] = ("in", sn)
	return frappe.get_all(
		EA,
		filters=filters,
		fields=[
			"name",
			"evaluation_session",
			"evaluator_user",
			"committee_role",
			"assignment_status",
			"modified",
		],
		order_by="modified desc",
	)


def get_conflict_declarations_pending(procuring_entity: str | None = None) -> list[dict[str, Any]]:
	filters: dict[str, Any] = {"declaration_status": "Pending"}
	sn = _session_names_for_entity(procuring_entity)
	if sn is not None:
		if not sn:
			return []
		filters["evaluation_session"] = ("in", sn)
	return frappe.get_all(
		COI,
		filters=filters,
		fields=[
			"name",
			"evaluation_session",
			"evaluator_user",
			"declaration_status",
			"declaration_datetime",
			"modified",
		],
		order_by="modified desc",
	)


def get_evaluation_sessions_in_progress(procuring_entity: str | None = None) -> list[dict[str, Any]]:
	filters: dict[str, Any] = {"status": "In Progress"}
	sn = _session_names_for_entity(procuring_entity)
	if sn is not None:
		if not sn:
			return []
		filters["name"] = ("in", sn)
	return frappe.get_all(
		ES,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"tender",
			"status",
			"workflow_state",
			"procuring_entity",
			"modified",
		],
		order_by="modified desc",
	)


def get_evaluation_reports_awaiting_submission(procuring_entity: str | None = None) -> list[dict[str, Any]]:
	filters: dict[str, Any] = {"status": ("in", ["Draft", "In Progress"])}
	sn = _session_names_for_entity(procuring_entity)
	if sn is not None:
		if not sn:
			return []
		filters["evaluation_session"] = ("in", sn)
	return frappe.get_all(
		ERPT,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"evaluation_session",
			"tender",
			"status",
			"modified",
		],
		order_by="modified desc",
	)


def get_disqualification_summary(procuring_entity: str | None = None) -> list[dict[str, Any]]:
	filters: dict[str, Any] = {}
	sn = _session_names_for_entity(procuring_entity)
	if sn is not None:
		if not sn:
			return []
		filters["evaluation_session"] = ("in", sn)
	return frappe.get_all(
		EDR,
		filters=filters,
		fields=[
			"name",
			"evaluation_session",
			"evaluation_stage",
			"bid_submission",
			"supplier",
			"status",
			"disqualification_reason_type",
			"modified",
		],
		order_by="modified desc",
		limit=500,
	)


def get_ranked_bid_summary(
	procuring_entity: str | None = None,
	evaluation_session: str | None = None,
) -> list[dict[str, Any]]:
	filters: dict[str, Any] = {"calculation_status": "Complete"}
	es = _norm(evaluation_session)
	if es:
		filters["evaluation_session"] = es
	else:
		sn = _session_names_for_entity(procuring_entity)
		if sn is not None:
			if not sn:
				return []
			filters["evaluation_session"] = ("in", sn)
	return frappe.get_all(
		EAR,
		filters=filters,
		fields=[
			"name",
			"evaluation_session",
			"bid_submission",
			"supplier",
			"technical_score_average",
			"financial_score",
			"combined_score",
			"preliminary_result",
			"overall_result",
			"ranking_position",
			"calculation_status",
			"modified",
		],
		order_by="evaluation_session asc, ranking_position asc",
		limit=500,
	)


def evaluation_queue_report_columns(keys: list[str]) -> list[dict[str, Any]]:
	return [{"fieldname": k, "label": k.replace("_", " ").title(), "fieldtype": "Data", "width": 120} for k in keys]


def evaluation_queue_row_values(row: dict[str, Any], keys: list[str]) -> list[Any]:
	return [row.get(k) for k in keys]


def evaluation_report_entity_filter() -> list[dict[str, Any]]:
	return [
		{
			"fieldname": "procuring_entity",
			"label": "Procuring Entity",
			"fieldtype": "Link",
			"options": "Procuring Entity",
			"default": "",
		}
	]
