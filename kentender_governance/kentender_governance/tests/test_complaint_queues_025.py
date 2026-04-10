# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-025: complaint queue queries and script reports."""

import importlib

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import run_test_db_cleanup

from kentender_governance.services.complaint_hold_services import apply_procurement_hold
from kentender_governance.services.complaint_intake_services import review_complaint_admissibility, submit_complaint
from kentender_governance.services.complaint_queue_queries import (
	get_complaint_appeals_register,
	get_complaint_decisions_register,
	get_complaints_awaiting_admissibility,
	get_complaints_under_review,
	get_complaints_with_active_hold,
)
from kentender_governance.tests.gov_test_utils import cleanup_complaint_chain

PREFIX = "_KT_GOV025"

_REPORT_MODULES = (
	"kentender_governance.kentender_governance.report.complaints_awaiting_admissibility.complaints_awaiting_admissibility",
	"kentender_governance.kentender_governance.report.complaints_under_review.complaints_under_review",
	"kentender_governance.kentender_governance.report.complaints_with_active_hold.complaints_with_active_hold",
	"kentender_governance.kentender_governance.report.complaint_decisions_register.complaint_decisions_register",
	"kentender_governance.kentender_governance.report.complaint_appeals_register.complaint_appeals_register",
)


def _exec_report(module_path: str, filters: dict | None = None):
	mod = importlib.import_module(module_path)
	return mod.execute(filters)


class TestComplaintQueues025(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(lambda: cleanup_complaint_chain(PREFIX))

	def tearDown(self):
		run_test_db_cleanup(lambda: cleanup_complaint_chain(PREFIX))
		super().tearDown()

	def test_KT_GOV025_queries_basic(self):
		pend = submit_complaint(
			business_id=f"{PREFIX}_P1",
			complaint_title="Q",
			complaint_type="Other",
			complainant_type="Citizen",
			complainant_name="P",
			complaint_summary="S",
			complaint_details="<p>D</p>",
			requested_remedy="R",
			received_by_user="Administrator",
			complainant_contact_email="p@example.com",
		)
		rows = get_complaints_awaiting_admissibility()
		self.assertTrue(any(r["name"] == pend.name for r in rows))

		review_complaint_admissibility(
			pend.name,
			"Admissible",
			admissibility_reason="OK",
			reviewed_by_user="Administrator",
		)
		under = get_complaints_under_review()
		self.assertTrue(any(r["name"] == pend.name for r in under))

		apply_procurement_hold(pend.name, affects_award_process=1, actor_user="Administrator")
		holds = get_complaints_with_active_hold()
		self.assertTrue(any(r["name"] == pend.name for r in holds))

	def test_KT_GOV025_script_reports_execute(self):
		doc = submit_complaint(
			business_id=f"{PREFIX}_REP",
			complaint_title="R",
			complaint_type="Other",
			complainant_type="Citizen",
			complainant_name="R",
			complaint_summary="S",
			complaint_details="<p>D</p>",
			requested_remedy="R",
			received_by_user="Administrator",
			complainant_contact_email="r@example.com",
		)
		cols, data = _exec_report(_REPORT_MODULES[0], {})
		self.assertTrue(len(cols) >= 3)
		self.assertTrue(any(doc.name in row for row in data))

		for path in _REPORT_MODULES[1:]:
			c, d = _exec_report(path, {})
			self.assertTrue(len(c) >= 1)
			self.assertIsInstance(d, list)
