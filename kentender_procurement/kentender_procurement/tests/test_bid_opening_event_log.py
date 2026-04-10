# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-051: Bid Opening Event Log."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
BOS = "Bid Opening Session"
BOEL = "Bid Opening Event Log"
BCP = "Budget Control Period"


def _cleanup_boel051():
	for sn in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_BOEL051_%")}, pluck="name") or []:
		frappe.db.delete(BOEL, {"bid_opening_session": sn})
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_BOEL051_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_BOEL051_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_BOEL051_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_BOEL051_PE"})


class TestBidOpeningEventLog051(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_boel051)
		self.entity = _make_entity("_KT_BOEL051_PE").insert()
		self.period = _bcp("_KT_BOEL051_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_boel051)
		super().tearDown()

	def test_valid_insert_append_only(self):
		t = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": "_KT_BOEL051_T1",
				"business_id": "_KT_BOEL051_T1-BIZ",
				"title": "BOEL051",
				"tender_number": "BOEL051-1",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		s = frappe.get_doc(
			{
				"doctype": BOS,
				"business_id": "_KT_BOEL051_S1",
				"tender": t.name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
			}
		).insert(ignore_permissions=True)
		doc = frappe.get_doc(
			{
				"doctype": BOEL,
				"bid_opening_session": s.name,
				"event_type": "Opening Started",
				"event_datetime": now_datetime(),
				"actor_user": "Administrator",
				"event_summary": "_KT_BOEL051_ opening started",
				"result_status": "Info",
				"event_hash": "sha256:boel051_test",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		doc.reload()
		self.assertRaises(frappe.ValidationError, doc.save)
