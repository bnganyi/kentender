# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-035: tender queue queries and script reports."""

import importlib

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.tender_queue_queries import (
	get_draft_tenders,
	get_published_tenders,
)

TENDER = "Tender"
BCP = "Budget Control Period"

_REPORT_MODULES = (
	"kentender_procurement.kentender_procurement.report.draft_tenders.draft_tenders",
	"kentender_procurement.kentender_procurement.report.tenders_under_review.tenders_under_review",
	"kentender_procurement.kentender_procurement.report.published_tenders.published_tenders",
	"kentender_procurement.kentender_procurement.report.tenders_closing_soon.tenders_closing_soon",
	"kentender_procurement.kentender_procurement.report.tender_amendments.tender_amendments",
	"kentender_procurement.kentender_procurement.report.tender_clarifications.tender_clarifications",
)


def _cleanup_tqr035():
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_TQR035_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_TQR035_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_TQR035_PE"})


class TestTenderScriptReports035(FrappeTestCase):
	def test_each_script_report_execute_returns_columns_and_data(self):
		for mod_path in _REPORT_MODULES:
			mod = importlib.import_module(mod_path)
			cols, data = mod.execute({})
			self.assertTrue(isinstance(cols, list) and len(cols) > 0, msg=mod_path)
			self.assertIsInstance(data, list, msg=mod_path)
			filters = mod.get_filters()
			self.assertIsInstance(filters, list)

	def test_closing_soon_report_accepts_days_ahead(self):
		mod = importlib.import_module(
			"kentender_procurement.kentender_procurement.report.tenders_closing_soon.tenders_closing_soon",
		)
		cols, data = mod.execute({"days_ahead": 30})
		self.assertTrue(len(cols) > 0)
		self.assertIsInstance(data, list)


class TestTenderQueueQueries035(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_tqr035)
		self.entity = _make_entity("_KT_TQR035_PE").insert()
		self.period = _bcp("_KT_TQR035_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_tqr035)
		super().tearDown()

	def test_draft_vs_published_filters(self):
		doc = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": "_KT_TQR035_TD",
				"business_id": "_KT_TQR035_B1",
				"title": "TQR035 draft",
				"tender_number": "TQR035-001",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		)
		doc.insert(ignore_permissions=True)
		draft_rows = get_draft_tenders(procuring_entity=self.entity.name)
		pub_rows = get_published_tenders(procuring_entity=self.entity.name)
		self.assertTrue(any(r.get("name") == doc.name for r in draft_rows))
		self.assertFalse(any(r.get("name") == doc.name for r in pub_rows))
