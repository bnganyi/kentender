# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""WF-005/006/007: resolve policy → template → route instance."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender.workflow_engine.policies import list_matching_policies


def resolve_route_for_object(
	doctype: str,
	docname: str,
	*,
	policy_name: str | None = None,
) -> str | None:
	"""Create a **KenTender Approval Route Instance** for *docname* and return its name.

	If *policy_name* is set, use that policy; otherwise pick the first matching active policy
	(by ``evaluation_order``, then ``policy_code``).
	Returns None if no policy/template could be resolved (caller may use a domain default).
	"""
	doc = frappe.get_doc(doctype, docname)
	if policy_name:
		if not frappe.db.exists("KenTender Workflow Policy", policy_name):
			return None
		policies = [policy_name] if policy_matches_active(policy_name, doc) else []
	else:
		policies = list_matching_policies(doc)
	if not policies:
		return None
	chosen = policies[0]
	pol = frappe.get_doc("KenTender Workflow Policy", chosen)
	template_id = (pol.linked_template or "").strip()
	if not template_id or not frappe.db.exists("KenTender Approval Route Template", template_id):
		return None
	template = frappe.get_doc("KenTender Approval Route Template", template_id)
	if not template.steps:
		frappe.throw(
			_("Approval route template {0} has no steps.").format(template_id),
			frappe.ValidationError,
		)
	instance = frappe.get_doc(
		{
			"doctype": "KenTender Approval Route Instance",
			"reference_doctype": doctype,
			"reference_docname": docname,
			"template_used": template.name,
			"status": "Active",
			"current_step_no": 1,
			"resolved_by_policy": pol.name,
			"resolved_on": now_datetime(),
			"route_steps": _steps_from_template(template),
		}
	)
	instance.insert(ignore_permissions=True)
	return instance.name


def get_or_create_active_route(
	doctype: str,
	docname: str,
	*,
	policy_name: str | None = None,
) -> str | None:
	"""Return an Active route instance name for the target, creating one if missing."""
	existing = get_active_route_instance(doctype, docname)
	if existing:
		return existing
	return resolve_route_for_object(doctype, docname, policy_name=policy_name)


def policy_matches_active(policy_name: str, doc: Document) -> bool:
	from kentender.workflow_engine.policies import policy_matches_document

	return policy_matches_document(policy_name, doc)


def _steps_from_template(template: Document) -> list[dict[str, Any]]:
	rows_raw = list(template.get("steps") or [])
	rows_raw.sort(key=lambda r: int(r.step_order or 0))
	rows: list[dict[str, Any]] = []
	for i, row in enumerate(rows_raw):
		rows.append(
			{
				"doctype": "KenTender Approval Route Step",
				"step_order": row.step_order,
				"step_name": row.step_name,
				"assigned_role": row.role_required,
				"status": "Active" if i == 0 else "Pending",
			}
		)
	return rows


def get_active_route_instance(doctype: str, docname: str) -> str | None:
	"""Return name of an Active route instance for this target, if any."""
	rows = frappe.get_all(
		"KenTender Approval Route Instance",
		filters={
			"reference_doctype": doctype,
			"reference_docname": docname,
			"status": "Active",
		},
		pluck="name",
		order_by="creation desc",
		limit=1,
	)
	return rows[0] if rows else None
