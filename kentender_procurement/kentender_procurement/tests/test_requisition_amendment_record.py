# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-007: Requisition Amendment Record DocType."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup

PR = "Purchase Requisition"
RAM = "Requisition Amendment Record"


def _minimal_pr(entity: str, currency: str, business_id: str = "_KT_PR07_R1"):
	return frappe.get_doc(
		{
			"doctype": PR,
			"name": business_id,
			"title": "Amendment linkage",
			"requisition_type": "Goods",
			"status": "Draft",
			"workflow_state": "Draft",
			"approval_status": "Draft",
			"procuring_entity": entity,
			"fiscal_year": "2026-2027",
			"currency": currency,
			"request_date": "2026-04-01",
			"priority_level": "Medium",
			"budget_reservation_status": "None",
			"planning_status": "Unplanned",
			"items": [
				{
					"doctype": "Purchase Requisition Item",
					"item_description": "One",
					"quantity": 1,
					"estimated_unit_cost": 1,
				}
			],
		}
	)


def _cleanup_pr07_data():
	for name in frappe.get_all(PR, filters={"name": ("like", "_KT_PR07_%")}, pluck="name") or []:
		frappe.db.delete(RAM, {"purchase_requisition": name})
		frappe.delete_doc(PR, name, force=True, ignore_permissions=True)
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_PR07_PE"})


class TestRequisitionAmendmentRecord(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_pr07_data)
		self.entity = _make_entity("_KT_PR07_PE").insert()
		self.pr = _minimal_pr(self.entity.name, self.currency)
		self.pr.insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_pr07_data)
		super().tearDown()

	def test_valid_create_and_linkage(self):
		am = frappe.get_doc(
			{
				"doctype": RAM,
				"purchase_requisition": self.pr.name,
				"amendment_type": "Quantity Change",
				"requested_by": frappe.session.user,
				"requested_on": "2026-04-02 09:00:00",
				"reason": "Adjust qty",
				"before_summary": '{"items":[{"idx":1,"quantity":1}]}',
				"after_summary": '{"items":[{"idx":1,"quantity":2}]}',
				"status": "Draft",
			}
		)
		am.insert(ignore_permissions=True)
		self.assertTrue(am.name)
		self.assertEqual(am.purchase_requisition, self.pr.name)

	def test_approved_requires_approver_fields(self):
		am = frappe.get_doc(
			{
				"doctype": RAM,
				"purchase_requisition": self.pr.name,
				"amendment_type": "Cancellation",
				"requested_by": frappe.session.user,
				"requested_on": "2026-04-02 10:00:00",
				"reason": "Cancel",
				"status": "Approved",
			}
		)
		self.assertRaises(frappe.ValidationError, am.insert)
