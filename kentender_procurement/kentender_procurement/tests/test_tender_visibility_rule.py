# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-028: Tender Visibility Rule."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
TVR = "Tender Visibility Rule"
BCP = "Budget Control Period"


def _cleanup_tvr028():
	for row in frappe.get_all(TVR, filters={"tender": ("like", "_KT_TVR028_%")}, pluck="name") or []:
		frappe.delete_doc(TVR, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_TVR028_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_TVR028_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_TVR028_PE"})


class TestTenderVisibilityRule(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_tvr028)
		self.entity = _make_entity("_KT_TVR028_PE").insert()
		self.period = _bcp("_KT_TVR028_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_tvr028)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "TVR tender",
				"tender_number": f"{name}-TN",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)

	def test_valid_rule_creation(self):
		t = self._tender("_KT_TVR028_T1")
		doc = frappe.get_doc(
			{
				"doctype": TVR,
				"tender": t.name,
				"rule_type": "Supplier Category",
				"rule_value": "CAT-001 / SME preferred",
				"status": "Draft",
				"remarks": "Smoke test rule",
			}
		)
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertEqual(doc.tender, t.name)
		self.assertIn("Supplier Category", doc.display_label or "")
		self.assertIn("CAT-001", doc.display_label or "")

	def test_invalid_tender_blocked(self):
		doc = frappe.get_doc(
			{
				"doctype": TVR,
				"tender": "NONEXISTENT_TENDER_TVR028",
				"rule_type": "Invitation List",
				"rule_value": "list-1",
				"status": "Draft",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)
