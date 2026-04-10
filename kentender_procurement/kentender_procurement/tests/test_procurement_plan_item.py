# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup

from kentender_budget.tests.test_budget_control_period import _bcp

PP = "Procurement Plan"
PPI = "Procurement Plan Item"
BCP = "Budget Control Period"


def _cleanup_ppi02_data():
	for name in frappe.get_all(PPI, filters={"name": ("like", "_KT_PPI02_%")}, pluck="name") or []:
		frappe.delete_doc(PPI, name, force=True, ignore_permissions=True)
	for name in frappe.get_all(PP, filters={"name": ("like", "_KT_PPI02_%")}, pluck="name") or []:
		frappe.delete_doc(PP, name, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_PPI02_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_PPI02_%")})


def _minimal_plan_kwargs(entity_name: str, bcp_name: str, currency: str, business_id: str, **extra):
	kw = {
		"doctype": PP,
		"name": business_id,
		"plan_title": "Plan for item tests",
		"workflow_state": "Draft",
		"status": "Draft",
		"approval_status": "Draft",
		"procuring_entity": entity_name,
		"fiscal_year": "2026-2027",
		"budget_control_period": bcp_name,
		"currency": currency,
		"version_no": 1,
		"allow_manual_items": 1,
	}
	kw.update(extra)
	return kw


def _minimal_item_kwargs(plan_name: str, entity_name: str, currency: str, business_id: str, **extra):
	kw = {
		"doctype": PPI,
		"name": business_id,
		"procurement_plan": plan_name,
		"title": "Test plan item",
		"procuring_entity": entity_name,
		"currency": currency,
		"status": "Draft",
		"origin_type": "Requisition Derived",
		"estimated_amount": 5000,
	}
	kw.update(extra)
	return kw


class TestProcurementPlanItem(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_ppi02_data)
		self.entity = _make_entity("_KT_PPI02_PE").insert()
		self.period = _bcp("_KT_PPI02_BCP", self.entity.name).insert()
		self.plan = frappe.get_doc(
			_minimal_plan_kwargs(self.entity.name, self.period.name, self.currency, "_KT_PPI02_PLN")
		).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_ppi02_data)
		super().tearDown()

	def test_valid_create(self):
		doc = frappe.get_doc(
			_minimal_item_kwargs(
				self.plan.name,
				self.entity.name,
				self.currency,
				"_KT_PPI02_I1",
			)
		)
		doc.insert()
		self.assertEqual(doc.name, "_KT_PPI02_I1")

	def test_rejects_wrong_entity_vs_plan(self):
		other = _make_entity("_KT_PPI02_PE2").insert()
		try:
			doc = frappe.get_doc(
				_minimal_item_kwargs(
					self.plan.name,
					other.name,
					self.currency,
					"_KT_PPI02_BADENT",
				)
			)
			self.assertRaises(frappe.ValidationError, doc.insert)
		finally:
			frappe.delete_doc("Procuring Entity", other.name, force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_rejects_wrong_currency_vs_plan(self):
		alt = "XTS_PPI02"
		if not frappe.db.exists("Currency", alt):
			frappe.get_doc({"doctype": "Currency", "currency_name": alt, "enabled": 1}).insert(
				ignore_permissions=True
			)
		try:
			doc = frappe.get_doc(
				_minimal_item_kwargs(
					self.plan.name,
					self.entity.name,
					alt,
					"_KT_PPI02_BADCUR",
				)
			)
			self.assertRaises(frappe.ValidationError, doc.insert)
		finally:
			if frappe.db.exists("Currency", alt):
				frappe.delete_doc("Currency", alt, force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_rejects_bad_schedule_order(self):
		doc = frappe.get_doc(
			_minimal_item_kwargs(
				self.plan.name,
				self.entity.name,
				self.currency,
				"_KT_PPI02_DATES",
				planned_publication_date="2026-08-01",
				planned_submission_deadline="2026-07-01",
			)
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_manual_rejected_when_plan_disallows_manual_items(self):
		plan_no_manual = frappe.get_doc(
			_minimal_plan_kwargs(
				self.entity.name,
				self.period.name,
				self.currency,
				"_KT_PPI02_PLN2",
				allow_manual_items=0,
			)
		).insert(ignore_permissions=True)
		try:
			doc = frappe.get_doc(
				_minimal_item_kwargs(
					plan_no_manual.name,
					self.entity.name,
					self.currency,
					"_KT_PPI02_MAN1",
					origin_type="Manual",
					manual_entry_justification="",
				)
			)
			self.assertRaises(frappe.ValidationError, doc.insert)
		finally:
			frappe.delete_doc(PP, plan_no_manual.name, force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_manual_ok_when_allowed_and_justified(self):
		doc = frappe.get_doc(
			_minimal_item_kwargs(
				self.plan.name,
				self.entity.name,
				self.currency,
				"_KT_PPI02_MAN2",
				origin_type="Manual",
				manual_entry_justification="Approved per delegation.",
			)
		)
		doc.insert()
		self.assertEqual(doc.name, "_KT_PPI02_MAN2")
