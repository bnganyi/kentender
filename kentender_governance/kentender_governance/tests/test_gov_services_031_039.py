# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-031–039: audit services, transparency DocTypes, reporting, dashboard."""

import json
import unittest

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender_governance.services.audit_query_response_services import (
	mark_audit_query_status,
	register_audit_response_submitted,
)
from kentender_governance.services.audit_reporting_queries import (
	get_draft_audit_responses,
	get_open_audit_actions,
	get_open_audit_queries,
)
from kentender_governance.services.disclosure_generation_services import (
	export_disclosure_dataset_rows,
	generate_public_disclosure,
)
from kentender_governance.services.reporting_export_services import execute_report_definition
from kentender_governance.services.transparency_dashboard_queries import get_transparency_dashboard_stats
from kentender_stores.tests.test_grn_doctypes_003_004 import cleanup_procurement_chain, minimal_procurement_contract

PREFIX = "_KT_GOV031"
PC = "Procurement Contract"
AQ = "KenTender Audit Query"
AR = "KenTender Audit Response"
PDR = "KenTender Public Disclosure Record"
DS = "KenTender Disclosure Dataset"
RD = "KenTender Report Definition"
REL = "KenTender Report Execution Log"


def _cleanup031():
	for dt in (REL, RD, PDR, DS):
		if not frappe.db.exists("DocType", dt):
			continue
		for name in frappe.get_all(dt, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
			frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
	for name in frappe.get_all(AR, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(AR, name, force=True, ignore_permissions=True)
	for name in frappe.get_all(AQ, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(AQ, name, force=True, ignore_permissions=True)
	cleanup_procurement_chain(PREFIX)


class TestGovServices031039(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(_cleanup031)

	def tearDown(self):
		run_test_db_cleanup(_cleanup031)
		super().tearDown()

	def test_KT_GOV031_audit_response_service(self):
		if not frappe.db.exists("DocType", AQ):
			raise unittest.SkipTest("Audit Query not installed.")
		q = frappe.get_doc(
			{
				"doctype": AQ,
				"business_id": f"{PREFIX}_Q",
				"query_title": "Check",
				"query_text": "<p>X</p>",
				"raised_by_user": "Administrator",
				"raised_on": frappe.utils.today(),
				"status": "Open",
			}
		).insert(ignore_permissions=True)
		r = frappe.get_doc(
			{
				"doctype": AR,
				"business_id": f"{PREFIX}_R",
				"audit_query": q.name,
				"response_text": "<p>OK</p>",
				"responded_by_user": "Administrator",
				"responded_on": frappe.utils.now_datetime(),
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		out = register_audit_response_submitted(r.name)
		self.assertEqual(out["query_status"], "Answered")
		open_names = [x["name"] for x in get_open_audit_queries(limit=500)]
		self.assertNotIn(q.name, open_names)

	def test_KT_GOV032_audit_reporting_queries(self):
		self.assertIsInstance(get_open_audit_queries(limit=5), list)
		self.assertIsInstance(get_draft_audit_responses(limit=5), list)
		self.assertIsInstance(get_open_audit_actions(limit=5), list)

	def test_KT_GOV037_generate_public_disclosure(self):
		if not frappe.db.exists("DocType", PC):
			raise unittest.SkipTest("Procurement Contract not available.")
		currency = _ensure_test_currency()
		entity = _make_entity(f"{PREFIX}_PE").insert()
		_bcp(f"{PREFIX}_BCP", entity.name).insert()
		pc = minimal_procurement_contract(PREFIX, "Z", entity.name, currency)
		out = generate_public_disclosure(
			PC,
			pc.name,
			disclosure_stage="Contract",
			business_id=f"{PREFIX}_PDR",
			status="Draft",
		)
		self.assertTrue(frappe.db.exists(PDR, out["public_disclosure"]))

	def test_KT_GOV034_export_dataset(self):
		if not frappe.db.exists("DocType", DS) or not frappe.db.exists("DocType", PC):
			raise unittest.SkipTest("Dataset / PC not available.")
		ds = frappe.get_doc(
			{
				"doctype": DS,
				"business_id": f"{PREFIX}_DS",
				"dataset_title": "Contracts",
				"source_doctype": PC,
				"field_allowlist_json": json.dumps(["business_id", "contract_title", "status"]),
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		exp = export_disclosure_dataset_rows(ds.name, limit=5)
		self.assertGreaterEqual(exp["row_count"], 0)
		self.assertIn("business_id", exp["fields"])

	def test_KT_GOV038_execute_report_definition(self):
		if not frappe.db.exists("DocType", RD) or not frappe.db.exists("DocType", "Report"):
			raise unittest.SkipTest("Report Definition / Report not available.")
		if not frappe.db.exists("Report", "Open Audit Queries"):
			raise unittest.SkipTest("Open Audit Queries report missing.")
		rd = frappe.get_doc(
			{
				"doctype": RD,
				"business_id": f"{PREFIX}_REP",
				"report_title": "Audit queue",
				"report_class": "Script Report",
				"standard_report": "Open Audit Queries",
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		out = execute_report_definition(rd.name, executed_by_user="Administrator")
		self.assertIn("execution_log", out)
		self.assertTrue(frappe.db.exists(REL, out["execution_log"]))

	def test_KT_GOV039_dashboard_stats(self):
		stats = get_transparency_dashboard_stats()
		self.assertIsInstance(stats, dict)
		self.assertIn("open_audit_queries", stats)

	def test_KT_GOV031_mark_query_status(self):
		if not frappe.db.exists("DocType", AQ):
			raise unittest.SkipTest("Audit Query not installed.")
		q = frappe.get_doc(
			{
				"doctype": AQ,
				"business_id": f"{PREFIX}_Q2",
				"query_title": "Y",
				"query_text": "<p>Z</p>",
				"raised_by_user": "Administrator",
				"raised_on": frappe.utils.today(),
				"status": "Open",
			}
		).insert(ignore_permissions=True)
		mark_audit_query_status(q.name, "Closed")
