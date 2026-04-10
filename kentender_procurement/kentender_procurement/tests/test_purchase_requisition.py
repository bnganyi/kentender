# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup

PR = "Purchase Requisition"


def _cleanup_pr01_data():
	for name in frappe.get_all(PR, filters={"name": ("like", "_KT_PR01_%")}, pluck="name") or []:
		frappe.delete_doc(PR, name, force=True, ignore_permissions=True)
	frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_PR01_%")})


def _minimal_requisition_kwargs(entity_name: str, currency: str, business_id: str = "_KT_PR01_R1"):
	return {
		"doctype": PR,
		"name": business_id,
		"title": "Test requisition",
		"requisition_type": "Goods",
		"status": "Draft",
		"workflow_state": "Draft",
		"approval_status": "Draft",
		"procuring_entity": entity_name,
		"fiscal_year": "2026-2027",
		"currency": currency,
		"request_date": "2026-04-01",
		"priority_level": "Medium",
		"budget_reservation_status": "None",
		"planning_status": "Unplanned",
	}


class TestPurchaseRequisition(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_pr01_data)
		self.entity = _make_entity("_KT_PR01_PE").insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_pr01_data)
		super().tearDown()

	def test_valid_create(self):
		doc = frappe.get_doc(_minimal_requisition_kwargs(self.entity.name, self.currency))
		doc.insert()
		self.assertEqual(doc.name, "_KT_PR01_R1")
		self.assertAlmostEqual(flt(doc.requested_amount), 0.0)

	def test_emergency_requires_justification(self):
		kw = _minimal_requisition_kwargs(self.entity.name, self.currency, business_id="_KT_PR01_R2")
		kw["is_emergency_request"] = 1
		doc = frappe.get_doc(kw)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_emergency_ok_with_justification(self):
		kw = _minimal_requisition_kwargs(self.entity.name, self.currency, business_id="_KT_PR01_R2B")
		kw["is_emergency_request"] = 1
		kw["emergency_justification"] = "Approved emergency per policy."
		doc = frappe.get_doc(kw)
		doc.insert()
		self.assertTrue(doc.name)

	def test_required_by_before_request_blocked(self):
		kw = _minimal_requisition_kwargs(self.entity.name, self.currency, business_id="_KT_PR01_R3")
		kw["request_date"] = "2026-06-01"
		kw["required_by_date"] = "2026-04-01"
		doc = frappe.get_doc(kw)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_line_total_calculated(self):
		kw = _minimal_requisition_kwargs(self.entity.name, self.currency, business_id="_KT_PR01_R4")
		kw["items"] = [
			{
				"doctype": "Purchase Requisition Item",
				"item_description": "Office chairs",
				"quantity": 10,
				"estimated_unit_cost": 2500,
			}
		]
		doc = frappe.get_doc(kw)
		doc.insert()
		doc.reload()
		self.assertEqual(len(doc.items), 1)
		self.assertAlmostEqual(flt(doc.items[0].line_total), 25000.0)
		self.assertAlmostEqual(flt(doc.requested_amount), 25000.0)

	def test_line_zero_quantity_blocked(self):
		kw = _minimal_requisition_kwargs(self.entity.name, self.currency, business_id="_KT_PR01_R5")
		kw["items"] = [
			{
				"doctype": "Purchase Requisition Item",
				"item_description": "Bad line",
				"quantity": 0,
				"estimated_unit_cost": 100,
			}
		]
		doc = frappe.get_doc(kw)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_line_zero_unit_cost_blocked(self):
		kw = _minimal_requisition_kwargs(self.entity.name, self.currency, business_id="_KT_PR01_R6")
		kw["items"] = [
			{
				"doctype": "Purchase Requisition Item",
				"item_description": "Bad line",
				"quantity": 5,
				"estimated_unit_cost": 0,
			}
		]
		doc = frappe.get_doc(kw)
		self.assertRaises(frappe.ValidationError, doc.insert)
