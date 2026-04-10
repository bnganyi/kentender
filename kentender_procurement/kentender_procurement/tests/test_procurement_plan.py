# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup

from kentender_budget.tests.test_budget_control_period import _bcp

PP = "Procurement Plan"
BCP = "Budget Control Period"


def _cleanup_pp01_data():
	for name in frappe.get_all(PP, filters={"name": ("like", "_KT_PP01_%")}, pluck="name") or []:
		frappe.delete_doc(PP, name, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_PP01_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_PP01_%")})


def _minimal_plan_kwargs(
	entity_name: str,
	bcp_name: str,
	currency: str,
	business_id: str = "_KT_PP01_001",
	**extra,
):
	kw = {
		"doctype": PP,
		"name": business_id,
		"plan_title": "Test procurement plan",
		"workflow_state": "Draft",
		"status": "Draft",
		"approval_status": "Draft",
		"procuring_entity": entity_name,
		"fiscal_year": "2026-2027",
		"budget_control_period": bcp_name,
		"currency": currency,
		"version_no": 1,
	}
	kw.update(extra)
	return kw


class TestProcurementPlan(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_pp01_data)
		self.entity = _make_entity("_KT_PP01_PE").insert()
		self.period = _bcp("_KT_PP01_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_pp01_data)
		super().tearDown()

	def test_valid_create(self):
		doc = frappe.get_doc(
			_minimal_plan_kwargs(self.entity.name, self.period.name, self.currency)
		)
		doc.insert()
		self.assertEqual(doc.name, "_KT_PP01_001")
		self.assertEqual(doc.status, "Draft")
		self.assertEqual(doc.approval_status, "Draft")

	def test_rejects_bcp_wrong_entity(self):
		other = _make_entity("_KT_PP01_PE2").insert()
		other_bcp = _bcp("_KT_PP01_BCP2", other.name).insert()
		try:
			doc = frappe.get_doc(
				_minimal_plan_kwargs(
					self.entity.name,
					other_bcp.name,
					self.currency,
					business_id="_KT_PP01_BADENT",
				)
			)
			self.assertRaises(frappe.ValidationError, doc.insert)
		finally:
			frappe.delete_doc(BCP, other_bcp.name, force=True, ignore_permissions=True)
			frappe.delete_doc("Procuring Entity", other.name, force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_rejects_fiscal_year_mismatch(self):
		doc = frappe.get_doc(
			_minimal_plan_kwargs(
				self.entity.name,
				self.period.name,
				self.currency,
				business_id="_KT_PP01_BADFY",
				fiscal_year="2099-2100",
			)
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_supersedes_requires_same_entity(self):
		v1 = frappe.get_doc(
			_minimal_plan_kwargs(self.entity.name, self.period.name, self.currency, business_id="_KT_PP01_V1")
		)
		v1.insert()
		other = _make_entity("_KT_PP01_PE3").insert()
		other_bcp = _bcp("_KT_PP01_BCP3", other.name).insert()
		try:
			v2 = frappe.get_doc(
				_minimal_plan_kwargs(
					other.name,
					other_bcp.name,
					self.currency,
					business_id="_KT_PP01_V2",
					supersedes_plan=v1.name,
				)
			)
			self.assertRaises(frappe.ValidationError, v2.insert)
		finally:
			frappe.delete_doc(BCP, other_bcp.name, force=True, ignore_permissions=True)
			frappe.delete_doc("Procuring Entity", other.name, force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_submitted_maps_summary_to_pending(self):
		doc = frappe.get_doc(
			_minimal_plan_kwargs(
				self.entity.name,
				self.period.name,
				self.currency,
				business_id="_KT_PP01_SUB",
				workflow_state="Submitted",
			)
		)
		doc.insert()
		self.assertEqual(doc.status, "Pending")
		self.assertEqual(doc.approval_status, "Submitted")
