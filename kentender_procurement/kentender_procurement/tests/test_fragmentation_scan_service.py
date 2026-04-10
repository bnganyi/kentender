# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-017: fragmentation scan service."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.fragmentation_scan_service import (
	FragmentationScanConfig,
	_refresh_fragmentation_flags_for_plan,
	run_fragmentation_scan_for_plan,
)

PP = "Procurement Plan"
PPI = "Procurement Plan Item"
PFRA = "Plan Fragmentation Alert"
BCP = "Budget Control Period"
PCAT = "Procurement Category"
PDEPT = "Procuring Department"


def _cleanup_fscan():
	for name in (
		frappe.get_all(PFRA, filters={"procurement_plan": ("like", "_KT_FSCAN_%")}, pluck="name") or []
	):
		frappe.delete_doc(PFRA, name, force=True, ignore_permissions=True)
	for row in frappe.get_all(PPI, filters={"name": ("like", "_KT_FSCAN_%")}, pluck="name") or []:
		frappe.delete_doc(PPI, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(PP, filters={"name": ("like", "_KT_FSCAN_%")}, pluck="name") or []:
		frappe.delete_doc(PP, row, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_FSCAN_%")})
	frappe.db.delete(PCAT, {"category_code": ("like", "_KT_FSCAN_%")})
	for dn in frappe.get_all(PDEPT, filters={"department_code": ("like", "_KT_FSCAN_%")}, pluck="name") or []:
		frappe.delete_doc(PDEPT, dn, force=True, ignore_permissions=True)
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_FSCAN_PE"})


class TestFragmentationScanService(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_fscan)
		self.entity = _make_entity("_KT_FSCAN_PE").insert()
		self.period = _bcp("_KT_FSCAN_BCP", self.entity.name).insert()
		self.plan = frappe.get_doc(
			{
				"doctype": PP,
				"name": "_KT_FSCAN_PP",
				"plan_title": "FSCAN plan",
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

	def tearDown(self):
		run_test_db_cleanup(_cleanup_fscan)
		super().tearDown()

	def _base_item(self, name: str, title: str, **extra):
		return frappe.get_doc(
			{
				"doctype": PPI,
				"name": name,
				"procurement_plan": self.plan.name,
				"title": title,
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"status": "Draft",
				"origin_type": "Requisition Derived",
				"estimated_amount": 1000,
				**extra,
			}
		).insert(ignore_permissions=True)

	def test_same_procurement_category_creates_similar_demand_alert(self):
		cat = frappe.get_doc(
			{
				"doctype": PCAT,
				"category_code": "_KT_FSCAN_CAT",
				"category_name": "FSCAN Test Category",
				"category_type": "Goods",
			}
		).insert(ignore_permissions=True)
		self._base_item("_KT_FSCAN_IA", "Alpha item", procurement_category=cat.name)
		self._base_item("_KT_FSCAN_IB", "Beta item", procurement_category=cat.name)

		res = run_fragmentation_scan_for_plan(self.plan.name)
		self.assertNotIn("error", res)
		self.assertGreaterEqual(res["alerts_created"], 1)
		alerts = frappe.get_all(
			PFRA,
			filters={"procurement_plan": self.plan.name},
			fields=["alert_type", "related_plan_item", "business_id"],
		)
		self.assertTrue(any(a["alert_type"] == "Similar Demand Split" for a in alerts))
		rel = next(a["related_plan_item"] for a in alerts if a["alert_type"] == "Similar Demand Split")
		self.assertEqual(rel, "_KT_FSCAN_IA")
		doc = frappe.get_doc(PPI, "_KT_FSCAN_IA")
		self.assertEqual(doc.fragmentation_alert_status, "Warning")
		self.assertGreater(doc.fragmentation_risk_score, 0)

	def test_same_requesting_department_duplicate_department_alert(self):
		dept = frappe.get_doc(
			{
				"doctype": PDEPT,
				"department_code": "_KT_FSCAN_DEPT",
				"department_name": "FSCAN Dept",
				"procuring_entity": self.entity.name,
			}
		).insert(ignore_permissions=True)
		self._base_item("_KT_FSCAN_IA", "Alpha item", requesting_department=dept.name)
		self._base_item("_KT_FSCAN_IB", "Beta item", requesting_department=dept.name)

		res = run_fragmentation_scan_for_plan(self.plan.name)
		self.assertNotIn("error", res)
		alerts = frappe.get_all(
			PFRA,
			filters={"procurement_plan": self.plan.name, "alert_type": "Duplicate Department Demand"},
		)
		self.assertEqual(len(alerts), 1)

	def test_schedule_window_overlap_duplicate_schedule_alert(self):
		self._base_item(
			"_KT_FSCAN_IA",
			"Schedule A",
			planned_publication_date="2026-06-01",
			planned_award_date="2026-08-01",
		)
		self._base_item(
			"_KT_FSCAN_IB",
			"Schedule B",
			planned_publication_date="2026-07-01",
			planned_award_date="2026-09-01",
		)

		res = run_fragmentation_scan_for_plan(self.plan.name)
		self.assertNotIn("error", res)
		alerts = frappe.get_all(
			PFRA,
			filters={"procurement_plan": self.plan.name, "alert_type": "Duplicate Schedule Window"},
		)
		self.assertEqual(len(alerts), 1)

	def test_second_scan_idempotent_skips_duplicates(self):
		cat = frappe.get_doc(
			{
				"doctype": PCAT,
				"category_code": "_KT_FSCAN_CAT2",
				"category_name": "FSCAN Cat 2",
				"category_type": "Goods",
			}
		).insert(ignore_permissions=True)
		self._base_item("_KT_FSCAN_IA", "Alpha item", procurement_category=cat.name)
		self._base_item("_KT_FSCAN_IB", "Beta item", procurement_category=cat.name)

		r1 = run_fragmentation_scan_for_plan(self.plan.name)
		self.assertNotIn("error", r1)
		self.assertGreater(r1["alerts_created"], 0)
		r2 = run_fragmentation_scan_for_plan(self.plan.name)
		self.assertEqual(r2["alerts_created"], 0)
		self.assertGreater(r2["alerts_skipped_duplicate"], 0)

	def test_item_cap_returns_error(self):
		self._base_item("_KT_FSCAN_I1", "Item one")
		self._base_item("_KT_FSCAN_I2", "Item two")
		self._base_item("_KT_FSCAN_I3", "Item three")
		cfg = FragmentationScanConfig(pairwise_item_cap=2)
		res = run_fragmentation_scan_for_plan(self.plan.name, config=cfg)
		self.assertEqual(res.get("error"), "item_count_exceeds_cap")

	def test_refresh_clears_ppi_when_no_open_alerts(self):
		self._base_item("_KT_FSCAN_IA", "Only item alpha")
		frappe.db.set_value(
			PPI,
			"_KT_FSCAN_IA",
			{"fragmentation_alert_status": "Warning", "fragmentation_risk_score": 0.5},
			update_modified=False,
		)
		_refresh_fragmentation_flags_for_plan(self.plan.name)
		doc = frappe.get_doc(PPI, "_KT_FSCAN_IA")
		self.assertEqual(doc.fragmentation_alert_status, "Not Assessed")
		self.assertEqual(doc.fragmentation_risk_score, 0)

	def test_dry_run_returns_candidates_without_db_writes(self):
		cat = frappe.get_doc(
			{
				"doctype": PCAT,
				"category_code": "_KT_FSCAN_CAT3",
				"category_name": "FSCAN Cat 3",
				"category_type": "Services",
			}
		).insert(ignore_permissions=True)
		self._base_item("_KT_FSCAN_IA", "Alpha item", procurement_category=cat.name)
		self._base_item("_KT_FSCAN_IB", "Beta item", procurement_category=cat.name)

		res = run_fragmentation_scan_for_plan(self.plan.name, dry_run=True)
		self.assertNotIn("error", res)
		self.assertGreater(res.get("candidates_count", 0), 0)
		self.assertFalse(
			frappe.db.exists(PFRA, {"procurement_plan": self.plan.name}),
		)
