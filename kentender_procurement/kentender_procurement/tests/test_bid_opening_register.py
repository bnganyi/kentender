# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-050: Bid Opening Register and lines."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
BS = "Bid Submission"
BCP = "Budget Control Period"


def _cleanup_bor050():
	for row in frappe.get_all(BOR, filters={"business_id": ("like", "_KT_BOR050_%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BS, filters={"business_id": ("like", "_KT_BOR050_%")}, pluck="name") or []:
		frappe.delete_doc(BS, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_BOR050_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_BOR050_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_BOR050_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_BOR050_PE"})


class TestBidOpeningRegister050(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_bor050)
		self.entity = _make_entity("_KT_BOR050_PE").insert()
		self.period = _bcp("_KT_BOR050_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_bor050)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "BOR050 tender",
				"tender_number": f"{name}-TN",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)

	def _session(self, tender_name: str):
		return frappe.get_doc(
			{
				"doctype": BOS,
				"business_id": f"_KT_BOR050_S_{tender_name}",
				"tender": tender_name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
			}
		).insert(ignore_permissions=True)

	def _draft_bid(self, tender_name: str, business_id: str):
		return frappe.get_doc(
			{
				"doctype": BS,
				"business_id": business_id,
				"tender": tender_name,
				"supplier": "BOR-SUP",
				"tender_lot_scope": "Whole Tender",
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
				"submission_version_no": 1,
			}
		).insert(ignore_permissions=True)

	def test_register_with_line(self):
		t = self._tender("_KT_BOR050_T1")
		s = self._session(t.name)
		b = self._draft_bid(t.name, "_KT_BOR050_B1")
		doc = frappe.get_doc(
			{
				"doctype": BOR,
				"business_id": "_KT_BOR050_RG1",
				"tender": t.name,
				"bid_opening_session": s.name,
				"status": "Draft",
				"register_lines": [
					{
						"bid_submission": b.name,
						"supplier": "BOR-SUP",
						"was_opened": 0,
						"was_excluded": 0,
					}
				],
			}
		).insert(ignore_permissions=True)
		self.assertEqual(len(doc.register_lines), 1)

	def test_line_bid_wrong_tender_blocked(self):
		t = self._tender("_KT_BOR050_T2")
		t2 = self._tender("_KT_BOR050_T2B")
		s = self._session(t.name)
		b = self._draft_bid(t2.name, "_KT_BOR050_B2")
		doc = frappe.get_doc(
			{
				"doctype": BOR,
				"business_id": "_KT_BOR050_RG2",
				"tender": t.name,
				"bid_opening_session": s.name,
				"status": "Draft",
				"register_lines": [
					{
						"bid_submission": b.name,
						"supplier": "X",
						"was_opened": 0,
						"was_excluded": 0,
					}
				],
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)
