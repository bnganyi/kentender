# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-031: create tender from plan item service."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.kentender_procurement.doctype.tender.tender import ORIGIN_FROM_PLAN_ITEM
from kentender_procurement.services.create_tender_from_plan_item import create_tender_from_plan_item

PP = "Procurement Plan"
PPI = "Procurement Plan Item"
PTTL = "Plan to Tender Link"
TENDER = "Tender"
BCP = "Budget Control Period"


def _cleanup_ctfpi():
	for row in frappe.get_all(PTTL, filters={"tender": ("like", "_KT_CTFPI_%")}, pluck="name") or []:
		frappe.delete_doc(PTTL, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_CTFPI_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	for pin in frappe.get_all(PPI, filters={"name": ("like", "_KT_CTFPI_%")}, pluck="name") or []:
		frappe.delete_doc(PPI, pin, force=True, ignore_permissions=True)
	for pp in frappe.get_all(PP, filters={"name": ("like", "_KT_CTFPI_%")}, pluck="name") or []:
		frappe.delete_doc(PP, pp, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_CTFPI_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_CTFPI_PE"})


class TestCreateTenderFromPlanItem(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_ctfpi)
		self.entity = _make_entity("_KT_CTFPI_PE").insert()
		self.period = _bcp("_KT_CTFPI_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_ctfpi)
		super().tearDown()

	def _plan(self, name: str, workflow_state: str):
		return frappe.get_doc(
			{
				"doctype": PP,
				"name": name,
				"plan_title": "CTFPI plan",
				"workflow_state": workflow_state,
				"status": "Draft",
				"approval_status": "Draft",
				"procuring_entity": self.entity.name,
				"fiscal_year": "2026-2027",
				"budget_control_period": self.period.name,
				"currency": self.currency,
				"version_no": 1,
				"allow_manual_items": 1,
			}
		).insert(ignore_permissions=True)

	def _item(self, name: str, plan_name: str, status: str, **extra):
		return frappe.get_doc(
			{
				"doctype": PPI,
				"name": name,
				"procurement_plan": plan_name,
				"title": "Ultrasound line",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"status": status,
				"origin_type": "Manual",
				"manual_entry_justification": "Test",
				"estimated_amount": 9000,
				"priority_level": "Medium",
				**extra,
			}
		).insert(ignore_permissions=True)

	def test_success_inherits_fields_and_creates_link(self):
		pp = self._plan("_KT_CTFPI_PP1", "Approved")
		pi = self._item(
			"_KT_CTFPI_I1",
			pp.name,
			"Approved",
			description="<p>Scope notes</p>",
			planned_publication_date="2026-05-01",
			planned_submission_deadline="2026-06-15",
		)
		out = create_tender_from_plan_item(
			pi.name,
			tender_name="_KT_CTFPI_T1",
			business_id="_KT_CTFPI_B1",
			tender_number="_KT_CTFPI_N1",
		)
		self.assertEqual(out["procurement_plan_item"], pi.name)
		self.assertEqual(out["tender"], "_KT_CTFPI_T1")
		self.assertTrue(out.get("plan_to_tender_link"))

		td = frappe.get_doc(TENDER, "_KT_CTFPI_T1")
		self.assertEqual(td.origin_type, ORIGIN_FROM_PLAN_ITEM)
		self.assertEqual(td.procurement_plan_item, pi.name)
		self.assertEqual(td.procurement_plan, pp.name)
		self.assertEqual(td.title, "Ultrasound line")
		self.assertEqual(td.procuring_entity, self.entity.name)
		self.assertEqual(td.currency, self.currency)
		self.assertEqual(float(td.estimated_amount), 9000.0)
		self.assertIn("Scope notes", td.description or "")
		self.assertTrue(td.short_description)
		self.assertEqual(td.plan_to_tender_link, out["plan_to_tender_link"])

		link = frappe.get_doc(PTTL, out["plan_to_tender_link"])
		self.assertEqual(link.status, "Active")
		self.assertEqual(link.link_type, "Direct")
		self.assertEqual(float(link.linked_amount), 9000.0)
		self.assertEqual(link.procurement_plan_item, pi.name)
		self.assertEqual(link.tender, "_KT_CTFPI_T1")

		pi.reload()
		self.assertEqual(pi.latest_tender, "_KT_CTFPI_T1")
		self.assertEqual(pi.tender_creation_status, "Created")

	def test_ineligible_blocked(self):
		pp = self._plan("_KT_CTFPI_PP2", "Draft")
		pi = self._item("_KT_CTFPI_I2", pp.name, "Approved")
		self.assertRaises(frappe.ValidationError, create_tender_from_plan_item, pi.name)
		self.assertEqual(frappe.db.count(TENDER, {"procurement_plan_item": pi.name}), 0)

	def test_duplicate_blocked(self):
		pp = self._plan("_KT_CTFPI_PP3", "Approved")
		pi = self._item("_KT_CTFPI_I3", pp.name, "Approved")
		create_tender_from_plan_item(
			pi.name,
			tender_name="_KT_CTFPI_T3",
			business_id="_KT_CTFPI_B3",
			tender_number="_KT_CTFPI_N3",
		)
		self.assertRaises(frappe.ValidationError, create_tender_from_plan_item, pi.name)
