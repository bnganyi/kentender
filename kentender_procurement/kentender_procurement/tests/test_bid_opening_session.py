# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-048: Bid Opening Session."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
BCP = "Budget Control Period"


def _cleanup_bos048():
	for row in frappe.get_all(BOR, filters={"business_id": ("like", "_KT_BOS048_%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_BOS048_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_BOS048_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_BOS048_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": ("in", ["_KT_BOS048_PE", "_KT_BOS048_PE2"])})


class TestBidOpeningSession048(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_bos048)
		self.entity = _make_entity("_KT_BOS048_PE").insert()
		self.period = _bcp("_KT_BOS048_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_bos048)
		super().tearDown()

	def _tender(self, name: str, **extra):
		kw = {
			"doctype": TENDER,
			"name": name,
			"business_id": f"{name}-BIZ",
			"title": "BOS048 tender",
			"tender_number": f"{name}-TN",
			"workflow_state": "Draft",
			"status": "Draft",
			"approval_status": "Draft",
			"origin_type": "Manual",
			"procuring_entity": self.entity.name,
			"currency": self.currency,
		}
		kw.update(extra)
		return frappe.get_doc(kw).insert(ignore_permissions=True)

	def _session(self, tender_name: str, business_id: str, **extra):
		kw = {
			"doctype": BOS,
			"business_id": business_id,
			"tender": tender_name,
			"procuring_entity": self.entity.name,
			"status": "Draft",
			"workflow_state": "Draft",
		}
		kw.update(extra)
		return frappe.get_doc(kw).insert(ignore_permissions=True)

	def test_valid_create(self):
		t = self._tender("_KT_BOS048_T1")
		doc = self._session(t.name, "_KT_BOS048_S1")
		self.assertTrue(doc.name)
		self.assertIn("_KT_BOS048_S1", doc.display_label or "")

	def test_blocks_second_active_session_same_tender(self):
		t = self._tender("_KT_BOS048_T2")
		self._session(t.name, "_KT_BOS048_S2A")
		doc2 = frappe.get_doc(
			{
				"doctype": BOS,
				"business_id": "_KT_BOS048_S2B",
				"tender": t.name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Scheduled",
			}
		)
		self.assertRaises(frappe.ValidationError, doc2.insert, ignore_permissions=True)

	def test_allows_new_session_after_terminal(self):
		t = self._tender("_KT_BOS048_T3")
		s1 = self._session(t.name, "_KT_BOS048_S3A")
		s1.workflow_state = "Completed"
		s1.status = "Completed"
		s1.save(ignore_permissions=True)
		s2 = self._session(t.name, "_KT_BOS048_S3B")
		self.assertTrue(s2.name)

	def test_procuring_entity_must_match_tender(self):
		t = self._tender("_KT_BOS048_T4")
		other = _make_entity("_KT_BOS048_PE2").insert()
		doc = frappe.get_doc(
			{
				"doctype": BOS,
				"business_id": "_KT_BOS048_S4",
				"tender": t.name,
				"procuring_entity": other.name,
				"status": "Draft",
				"workflow_state": "Draft",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_opening_register_link_matches_tender_and_session(self):
		t = self._tender("_KT_BOS048_T5")
		s = self._session(t.name, "_KT_BOS048_S5")
		reg = frappe.get_doc(
			{
				"doctype": BOR,
				"business_id": "_KT_BOS048_RG1",
				"tender": t.name,
				"bid_opening_session": s.name,
			}
		).insert(ignore_permissions=True)
		s.reload()
		s.opening_register = reg.name
		s.save(ignore_permissions=True)
		self.assertEqual(s.opening_register, reg.name)
