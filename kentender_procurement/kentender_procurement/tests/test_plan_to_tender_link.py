# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-021: Plan to Tender Link + tender eligibility."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.plan_item_tender_eligibility import get_plan_item_tender_eligibility

PP = "Procurement Plan"
PPI = "Procurement Plan Item"
PTTL = "Plan to Tender Link"
TENDER = "Tender"
BCP = "Budget Control Period"


def _cleanup_pttl():
	for row in frappe.get_all(PTTL, filters={"tender": ("like", "_KT_PTTL_%")}, pluck="name") or []:
		frappe.delete_doc(PTTL, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_PTTL_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	for pin in frappe.get_all(PPI, filters={"name": ("like", "_KT_PTTL_%")}, pluck="name") or []:
		frappe.delete_doc(PPI, pin, force=True, ignore_permissions=True)
	for pp in frappe.get_all(PP, filters={"name": ("like", "_KT_PTTL_%")}, pluck="name") or []:
		frappe.delete_doc(PP, pp, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_PTTL_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_PTTL_PE"})


class TestPlanToTenderLink(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_pttl)
		self.entity = _make_entity("_KT_PTTL_PE").insert()
		self.period = _bcp("_KT_PTTL_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_pttl)
		super().tearDown()

	def _plan(self, name: str, workflow_state: str, **extra):
		return frappe.get_doc(
			{
				"doctype": PP,
				"name": name,
				"plan_title": "PTTL plan",
				"workflow_state": workflow_state,
				"status": "Draft",
				"approval_status": "Draft",
				"procuring_entity": self.entity.name,
				"fiscal_year": "2026-2027",
				"budget_control_period": self.period.name,
				"currency": self.currency,
				"version_no": 1,
				"allow_manual_items": 1,
				**extra,
			}
		).insert(ignore_permissions=True)

	def _item(self, name: str, plan_name: str, status: str, **extra):
		return frappe.get_doc(
			{
				"doctype": PPI,
				"name": name,
				"procurement_plan": plan_name,
				"title": "Line",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"status": status,
				"origin_type": "Manual",
				"manual_entry_justification": "Test",
				"estimated_amount": 1000,
				"priority_level": "Medium",
				**extra,
			}
		).insert(ignore_permissions=True)

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "PTTL tender",
				"tender_number": f"{name}-TN",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)

	def test_eligible_when_plan_approved_and_item_approved(self):
		pp = self._plan("_KT_PTTL_PP1", "Approved")
		pi = self._item("_KT_PTTL_I1", pp.name, "Approved")
		info = get_plan_item_tender_eligibility(pi.name)
		self.assertTrue(info["eligible"])
		self.assertFalse(info["reasons"])

	def test_ineligible_when_plan_draft(self):
		pp = self._plan("_KT_PTTL_PP2", "Draft")
		pi = self._item("_KT_PTTL_I2", pp.name, "Approved")
		info = get_plan_item_tender_eligibility(pi.name)
		self.assertFalse(info["eligible"])
		self.assertTrue(any("workflow" in r.lower() or "approved or active" in r.lower() for r in info["reasons"]))

	def test_ineligible_when_item_draft(self):
		pp = self._plan("_KT_PTTL_PP3", "Active")
		pi = self._item("_KT_PTTL_I3", pp.name, "Draft")
		info = get_plan_item_tender_eligibility(pi.name)
		self.assertFalse(info["eligible"])

	def test_ineligible_when_fragmentation_warning(self):
		pp = self._plan("_KT_PTTL_PP4", "Approved")
		pi = self._item("_KT_PTTL_I4", pp.name, "Approved")
		frappe.db.set_value(
			PPI,
			pi.name,
			{"fragmentation_alert_status": "Warning"},
			update_modified=False,
		)
		info = get_plan_item_tender_eligibility(pi.name)
		self.assertFalse(info["eligible"])
		self.assertTrue(any("fragmentation" in r.lower() for r in info["reasons"]))

	def test_create_active_link_basics(self):
		pp = self._plan("_KT_PTTL_PP5", "Approved")
		pi = self._item("_KT_PTTL_I5", pp.name, "Approved")
		self._tender("_KT_PTTL_T1")
		doc = frappe.get_doc(
			{
				"doctype": PTTL,
				"procurement_plan_item": pi.name,
				"tender": "_KT_PTTL_T1",
				"link_type": "Direct",
				"linked_amount": 100,
				"linked_on": "2026-04-11 10:00:00",
				"status": "Active",
			}
		)
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertIn(pi.name, doc.display_label or "")
		self.assertIn("_KT_PTTL_T1", doc.display_label or "")

	def test_active_link_blocked_when_item_ineligible(self):
		pp = self._plan("_KT_PTTL_PP6", "Draft")
		pi = self._item("_KT_PTTL_I6", pp.name, "Approved")
		self._tender("_KT_PTTL_T2")
		doc = frappe.get_doc(
			{
				"doctype": PTTL,
				"procurement_plan_item": pi.name,
				"tender": "_KT_PTTL_T2",
				"link_type": "Consolidated Tender",
				"linked_amount": 50,
				"linked_on": "2026-04-11 11:00:00",
				"status": "Active",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)
