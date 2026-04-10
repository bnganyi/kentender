# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Ensure default Purchase Requisition workflow policy for Minimal Golden seed (WF-011)."""

from __future__ import annotations

import frappe

from kentender.permissions.registry import UAT_ROLE

PR = "Purchase Requisition"
POLICY_CODE = "MG_DEFAULT_PR"
TEMPLATE_CODE = "MG_PR_HOD_FIN"


def ensure_minimal_golden_pr_workflow_policy() -> None:
	"""Idempotent: HOD then Finance approval route per spec v2 §7.1."""
	if frappe.db.exists("KenTender Workflow Policy", {"policy_code": POLICY_CODE}):
		return
	tpl = frappe.get_doc(
		{
			"doctype": "KenTender Approval Route Template",
			"template_code": TEMPLATE_CODE,
			"template_name": "Minimal Golden — PR HOD then Finance",
			"object_type": PR,
			"steps": [
				{
					"doctype": "KenTender Approval Route Template Step",
					"step_order": 1,
					"step_name": "HOD",
					"actor_type": "Role",
					"role_required": UAT_ROLE.HOD.value,
				},
				{
					"doctype": "KenTender Approval Route Template Step",
					"step_order": 2,
					"step_name": "Finance",
					"actor_type": "Role",
					"role_required": UAT_ROLE.FINANCE.value,
				},
			],
		}
	)
	tpl.insert(ignore_permissions=True)
	pol = frappe.get_doc(
		{
			"doctype": "KenTender Workflow Policy",
			"policy_code": POLICY_CODE,
			"applies_to_doctype": PR,
			"linked_template": tpl.name,
			"active": 1,
			"evaluation_order": 10,
		}
	)
	pol.insert(ignore_permissions=True)
