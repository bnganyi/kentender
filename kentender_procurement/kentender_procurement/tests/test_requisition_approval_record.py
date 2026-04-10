# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup

PR = "Purchase Requisition"
RAR = "Requisition Approval Record"


def _minimal_requisition_kwargs(entity_name: str, currency: str, business_id: str = "_KT_PR04_R1"):
	return {
		"doctype": PR,
		"name": business_id,
		"title": "RAR linkage test",
		"requisition_type": "Goods",
		"status": "Pending",
		"workflow_state": "Pending HOD Approval",
		"approval_status": "Pending HOD Approval",
		"procuring_entity": entity_name,
		"fiscal_year": "2026-2027",
		"currency": currency,
		"request_date": "2026-04-01",
		"priority_level": "Medium",
		"budget_reservation_status": "None",
		"planning_status": "Unplanned",
		"items": [
			{
				"doctype": "Purchase Requisition Item",
				"item_description": "Test item",
				"quantity": 1,
				"estimated_unit_cost": 100,
			}
		],
	}


def _cleanup_pr04_rar_data():
	for name in frappe.get_all(PR, filters={"name": ("like", "_KT_PR04_R%")}, pluck="name") or []:
		frappe.db.delete(RAR, {"purchase_requisition": name})
		frappe.delete_doc(PR, name, force=True, ignore_permissions=True)
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_PR04_PE"})


class TestRequisitionApprovalRecord(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_pr04_rar_data)
		self.entity = _make_entity("_KT_PR04_PE").insert()
		self.pr = frappe.get_doc(_minimal_requisition_kwargs(self.entity.name, self.currency))
		self.pr.insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_pr04_rar_data)
		super().tearDown()

	def test_valid_create_and_linkage(self):
		rar = frappe.get_doc(
			{
				"doctype": RAR,
				"purchase_requisition": self.pr.name,
				"workflow_step": "HOD",
				"decision_level": "L1",
				"approver_user": frappe.session.user,
				"action_type": "Approve",
				"action_datetime": "2026-04-02 10:00:00",
				"comments": "OK",
			}
		)
		rar.insert(ignore_permissions=True)
		self.assertTrue(rar.name)
		self.assertEqual(rar.purchase_requisition, self.pr.name)
		rar.reload()
		self.assertEqual(rar.action_type, "Approve")

	def test_append_only_update_blocked(self):
		rar = frappe.get_doc(
			{
				"doctype": RAR,
				"purchase_requisition": self.pr.name,
				"workflow_step": "HOD",
				"decision_level": "L1",
				"approver_user": frappe.session.user,
				"action_type": "Reject",
				"action_datetime": "2026-04-02 11:00:00",
			}
		)
		rar.insert(ignore_permissions=True)
		rar.comments = "changed"
		self.assertRaises(frappe.ValidationError, rar.save)
