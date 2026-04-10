# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-047: bid queue queries and script reports."""

import importlib

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, now_datetime

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.bid_queue_queries import (
	get_bids_awaiting_opening,
	get_draft_bids,
	get_submission_receipts,
	get_submitted_bids,
	get_withdrawn_bids,
)

TENDER = "Tender"
BS = "Bid Submission"
BR = "Bid Receipt"
BCP = "Budget Control Period"

_REPORT_MODULES = (
	"kentender_procurement.kentender_procurement.report.draft_bids.draft_bids",
	"kentender_procurement.kentender_procurement.report.submitted_bids.submitted_bids",
	"kentender_procurement.kentender_procurement.report.withdrawn_bids.withdrawn_bids",
	"kentender_procurement.kentender_procurement.report.bids_awaiting_opening.bids_awaiting_opening",
	"kentender_procurement.kentender_procurement.report.submission_receipts.submission_receipts",
)


def _cleanup_bqr047():
	for row in frappe.get_all(BR, filters={"business_id": ("like", "_KT_BQR047_%")}, pluck="name") or []:
		frappe.delete_doc(BR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BS, filters={"business_id": ("like", "_KT_BQR047_%")}, pluck="name") or []:
		frappe.delete_doc(BS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_BQR047_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_BQR047_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_BQR047_PE"})


class TestBidScriptReports047(FrappeTestCase):
	def test_each_script_report_execute_returns_columns_and_data(self):
		for mod_path in _REPORT_MODULES:
			mod = importlib.import_module(mod_path)
			cols, data = mod.execute({})
			self.assertTrue(isinstance(cols, list) and len(cols) > 0, msg=mod_path)
			self.assertIsInstance(data, list, msg=mod_path)
			filters = mod.get_filters()
			self.assertIsInstance(filters, list)


class TestBidQueueQueries047(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_bqr047)
		self.entity = _make_entity("_KT_BQR047_PE").insert()
		self.period = _bcp("_KT_BQR047_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_bqr047)
		super().tearDown()

	def _tender(self, name: str, **extra):
		kw = {
			"doctype": TENDER,
			"name": name,
			"business_id": f"{name}-BIZ",
			"title": "BQR047 tender",
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

	def _bid(self, tender_name: str, business_id: str, **extra):
		kw = {
			"doctype": BS,
			"business_id": business_id,
			"tender": tender_name,
			"supplier": "BQR-SUP",
			"tender_lot_scope": "Whole Tender",
			"procuring_entity": self.entity.name,
			"status": "Draft",
			"workflow_state": "Draft",
			"submission_version_no": 1,
			"active_submission_flag": 1,
		}
		kw.update(extra)
		return frappe.get_doc(kw).insert(ignore_permissions=True)

	def _force_submitted_bid(self, name: str) -> None:
		"""Set final submission fields without running submit service (read-side queue tests only)."""
		frappe.db.set_value(
			BS,
			name,
			{
				"workflow_state": "Submitted",
				"status": "Submitted",
				"is_final_submission": 1,
				"sealed_status": "Sealed",
				"submitted_on": now_datetime(),
			},
			update_modified=False,
		)

	def test_draft_submitted_withdrawn_and_receipt_filters(self):
		t = self._tender("_KT_BQR047_T1")
		draft = self._bid(t.name, "_KT_BQR047_BD1")
		sub = self._bid(t.name, "_KT_BQR047_BS1")
		self._force_submitted_bid(sub.name)
		wd = self._bid(
			t.name,
			"_KT_BQR047_BW1",
			workflow_state="Withdrawn",
			status="Withdrawn",
			withdrawn_on=now_datetime(),
			active_submission_flag=0,
		)
		now = now_datetime()
		rc = frappe.get_doc(
			{
				"doctype": BR,
				"business_id": "_KT_BQR047_RC1",
				"receipt_no": "BQR047-RC-001",
				"bid_submission": sub.name,
				"tender": t.name,
				"supplier": "BQR-SUP",
				"issued_on": now,
				"submission_timestamp": now,
				"submission_hash": "sha256:sub_bqr047",
				"receipt_hash": "sha256:rec_bqr047",
				"issued_to_user": "Administrator",
				"status": "Issued",
			}
		).insert(ignore_permissions=True)

		ent = self.entity.name
		self.assertTrue(any(r.get("name") == draft.name for r in get_draft_bids(procuring_entity=ent)))
		self.assertTrue(any(r.get("name") == sub.name for r in get_submitted_bids(procuring_entity=ent)))
		self.assertTrue(any(r.get("name") == wd.name for r in get_withdrawn_bids(procuring_entity=ent)))
		self.assertTrue(any(r.get("name") == rc.name for r in get_submission_receipts(procuring_entity=ent)))

	def test_bids_awaiting_opening_requires_published_tender(self):
		t = self._tender("_KT_BQR047_T2")
		opening = add_days(now_datetime(), 7)
		frappe.db.set_value(
			TENDER,
			t.name,
			{
				"workflow_state": "Published",
				"status": "Active",
				"approval_status": "Published",
				"submission_status": "Open",
				"opening_datetime": opening,
			},
			update_modified=False,
		)
		b = self._bid(t.name, "_KT_BQR047_BO1")
		self._force_submitted_bid(b.name)
		frappe.db.set_value(
			BS,
			b.name,
			{"is_opening_visible": 0, "sealed_status": "Sealed"},
			update_modified=False,
		)
		ent = self.entity.name
		rows = get_bids_awaiting_opening(procuring_entity=ent)
		self.assertTrue(any(r.get("name") == b.name for r in rows))
