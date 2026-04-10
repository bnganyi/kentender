# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-009: Requisition Planning Link and planning derivation."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender_procurement.services.requisition_planning_derivation import (
	STATUS_LINKED,
	STATUS_PARTIAL,
	STATUS_PLANNED,
	STATUS_UNPLANNED,
)

PR = "Purchase Requisition"
RPL = "Requisition Planning Link"
PP = "Procurement Plan"
PPI = "Procurement Plan Item"
BCP = "Budget Control Period"


def _minimal_pr(entity: str, currency: str, business_id: str, qty: float = 10, unit: float = 10):
	return frappe.get_doc(
		{
			"doctype": PR,
			"name": business_id,
			"title": "Planning test",
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
					"item_description": "Line",
					"quantity": qty,
					"estimated_unit_cost": unit,
				}
			],
		}
	)


def _link(pr_name: str, amount: float, **extra):
	row = {
		"doctype": RPL,
		"purchase_requisition": pr_name,
		"linked_amount": amount,
		"linked_on": "2026-05-01 10:00:00",
		"status": "Active",
	}
	row.update(extra)
	doc = frappe.get_doc(row)
	doc.insert(ignore_permissions=True)
	return doc


def _cleanup_pr09_data():
	for pr in frappe.get_all(PR, filters={"name": ("like", "_KT_PR09_%")}, pluck="name") or []:
		frappe.db.delete(RPL, {"purchase_requisition": pr})
		frappe.delete_doc(PR, pr, force=True, ignore_permissions=True)
	for pin in frappe.get_all(PPI, filters={"name": ("like", "_KT_PR09_%")}, pluck="name") or []:
		frappe.delete_doc(PPI, pin, force=True, ignore_permissions=True)
	for pp in frappe.get_all(PP, filters={"name": ("like", "_KT_PR09_%")}, pluck="name") or []:
		frappe.delete_doc(PP, pp, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_PR09_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_PR09_PE"})


class TestRequisitionPlanningDerivation(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_pr09_data)
		self.entity = _make_entity("_KT_PR09_PE").insert()
		self.period = _bcp("_KT_PR09_BCP", self.entity.name).insert()
		self.stub_plan = frappe.get_doc(
			{
				"doctype": PP,
				"name": "_KT_PR09_PP1",
				"plan_title": "Stub plan for link test",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"procuring_entity": self.entity.name,
				"fiscal_year": "2026-2027",
				"budget_control_period": self.period.name,
				"currency": self.currency,
				"version_no": 1,
			}
		).insert(ignore_permissions=True)
		self.stub_item = frappe.get_doc(
			{
				"doctype": PPI,
				"name": "_KT_PR09_PPI1",
				"procurement_plan": self.stub_plan.name,
				"title": "Stub plan item for link test",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"status": "Draft",
				"origin_type": "Requisition Derived",
				"estimated_amount": 1000,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_pr09_data)
		super().tearDown()

	def test_no_links_unplanned(self):
		doc = _minimal_pr(self.entity.name, self.currency, "_KT_PR09_P1")
		doc.insert()
		doc.reload()
		self.assertEqual(doc.planning_status, STATUS_UNPLANNED)
		self.assertAlmostEqual(flt(doc.planned_amount), 0.0)
		self.assertAlmostEqual(flt(doc.unplanned_amount), 100.0)

	def test_partial_planning(self):
		doc = _minimal_pr(self.entity.name, self.currency, "_KT_PR09_P2")
		doc.insert()
		_link(doc.name, 40.0)
		doc.reload()
		self.assertEqual(doc.planning_status, STATUS_PARTIAL)
		self.assertAlmostEqual(flt(doc.planned_amount), 40.0)
		self.assertAlmostEqual(flt(doc.unplanned_amount), 60.0)

	def test_full_coverage_planned(self):
		doc = _minimal_pr(self.entity.name, self.currency, "_KT_PR09_P3")
		doc.insert()
		_link(doc.name, 40.0)
		_link(doc.name, 60.0)
		doc.reload()
		self.assertEqual(doc.planning_status, STATUS_PLANNED)
		self.assertAlmostEqual(flt(doc.planned_amount), 100.0)
		self.assertAlmostEqual(flt(doc.unplanned_amount), 0.0)

	def test_full_coverage_linked_when_plan_ref(self):
		doc = _minimal_pr(self.entity.name, self.currency, "_KT_PR09_P4")
		doc.insert()
		_link(
			doc.name,
			100.0,
			procurement_plan=self.stub_plan.name,
			procurement_plan_item=self.stub_item.name,
		)
		doc.reload()
		self.assertEqual(doc.planning_status, STATUS_LINKED)
		self.assertEqual(doc.latest_procurement_plan, self.stub_plan.name)
		self.assertEqual(doc.latest_procurement_plan_item, self.stub_item.name)

	def test_released_link_ignored(self):
		doc = _minimal_pr(self.entity.name, self.currency, "_KT_PR09_P5")
		doc.insert()
		lnk = _link(doc.name, 100.0)
		doc.reload()
		self.assertEqual(doc.planning_status, STATUS_PLANNED)
		lnk.status = "Released"
		lnk.save(ignore_permissions=True)
		doc.reload()
		self.assertEqual(doc.planning_status, STATUS_UNPLANNED)
		self.assertAlmostEqual(flt(doc.planned_amount), 0.0)

	def test_trash_link_refreshes_parent(self):
		doc = _minimal_pr(self.entity.name, self.currency, "_KT_PR09_P6")
		doc.insert()
		lnk = _link(doc.name, 50.0)
		doc.reload()
		self.assertEqual(doc.planning_status, STATUS_PARTIAL)
		frappe.delete_doc(RPL, lnk.name, force=True, ignore_permissions=True)
		doc.reload()
		self.assertEqual(doc.planning_status, STATUS_UNPLANNED)

	def test_linked_amount_positive_required(self):
		doc = _minimal_pr(self.entity.name, self.currency, "_KT_PR09_P7")
		doc.insert()
		bad = frappe.get_doc(
			{
				"doctype": RPL,
				"purchase_requisition": doc.name,
				"linked_amount": 0,
				"linked_on": "2026-05-01 10:00:00",
				"status": "Active",
			}
		)
		self.assertRaises(frappe.ValidationError, bad.insert)

	def test_second_active_link_over_requested_rejected(self):
		doc = _minimal_pr(self.entity.name, self.currency, "_KT_PR09_P8")
		doc.insert()
		_link(doc.name, 70.0)
		second = frappe.get_doc(
			{
				"doctype": RPL,
				"purchase_requisition": doc.name,
				"linked_amount": 40.0,
				"linked_on": "2026-05-01 11:00:00",
				"status": "Active",
			}
		)
		self.assertRaises(frappe.ValidationError, second.insert)

	def test_update_active_link_over_requested_rejected(self):
		doc = _minimal_pr(self.entity.name, self.currency, "_KT_PR09_P9")
		doc.insert()
		lnk = _link(doc.name, 50.0)
		lnk.reload()
		lnk.linked_amount = 101.0
		self.assertRaises(frappe.ValidationError, lnk.save)

	def test_line_mode_derives_linked_amount_and_rollups(self):
		doc = _minimal_pr(self.entity.name, self.currency, "_KT_PR09_P10")
		doc.insert()
		doc.reload()
		line_name = doc.items[0].name
		row = frappe.get_doc(
			{
				"doctype": RPL,
				"purchase_requisition": doc.name,
				"purchase_requisition_item": line_name,
				"linked_quantity": 6.0,
				"linked_amount": 0,
				"linked_on": "2026-05-01 12:00:00",
				"status": "Active",
			}
		)
		row.insert(ignore_permissions=True)
		self.assertAlmostEqual(flt(row.linked_amount), 60.0)
		doc.reload()
		self.assertAlmostEqual(flt(doc.items[0].planned_quantity), 6.0)
		self.assertAlmostEqual(flt(doc.items[0].remaining_quantity), 4.0)

	def test_line_over_quantity_rejected(self):
		doc = _minimal_pr(self.entity.name, self.currency, "_KT_PR09_P11")
		doc.insert()
		doc.reload()
		line_name = doc.items[0].name
		_link_for_line = lambda qty: frappe.get_doc(
			{
				"doctype": RPL,
				"purchase_requisition": doc.name,
				"purchase_requisition_item": line_name,
				"linked_quantity": qty,
				"linked_amount": 0,
				"linked_on": "2026-05-01 13:00:00",
				"status": "Active",
			}
		).insert(ignore_permissions=True)

		_link_for_line(6.0)
		second = frappe.get_doc(
			{
				"doctype": RPL,
				"purchase_requisition": doc.name,
				"purchase_requisition_item": line_name,
				"linked_quantity": 5.0,
				"linked_amount": 0,
				"linked_on": "2026-05-01 14:00:00",
				"status": "Active",
			}
		)
		self.assertRaises(frappe.ValidationError, second.insert)
