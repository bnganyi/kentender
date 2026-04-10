# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-024: execute complaint decision (complete actions)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import run_test_db_cleanup

from kentender_governance.services.complaint_action_services import execute_complaint_decision
from kentender_governance.services.complaint_intake_services import review_complaint_admissibility, submit_complaint
from kentender_governance.services.complaint_review_services import (
	assign_complaint_reviewer,
	issue_complaint_decision,
	submit_complaint_review,
)
from kentender_governance.tests.gov_test_utils import cleanup_complaint_chain

PREFIX = "_KT_GOV024"
CA = "Complaint Action"
CD = "Complaint Decision"


def _full_decision(business_id: str, decision_business_id: str):
	cdoc = submit_complaint(
		business_id=business_id,
		complaint_title="Exec test",
		complaint_type="Other",
		complainant_type="Citizen",
		complainant_name="C",
		complaint_summary="S",
		complaint_details="<p>D</p>",
		requested_remedy="R",
		received_by_user="Administrator",
		complainant_contact_email="c@example.com",
	)
	cid = cdoc.name
	review_complaint_admissibility(
		cid,
		"Admissible",
		admissibility_reason="OK",
		reviewed_by_user="Administrator",
	)
	assign_complaint_reviewer(cid, "Administrator", actor_user="Administrator")
	submit_complaint_review(
		cid,
		"Summary",
		"Dismiss",
		reviewer_user="Administrator",
	)
	return issue_complaint_decision(
		cid,
		decision_business_id=decision_business_id,
		decision_result="Dismissed",
		decision_summary="Final",
		decided_by_user="Administrator",
	)


class TestComplaintActionServices024(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(lambda: cleanup_complaint_chain(PREFIX))

	def tearDown(self):
		run_test_db_cleanup(lambda: cleanup_complaint_chain(PREFIX))
		super().tearDown()

	def test_KT_GOV024_execute_completes_actions(self):
		d = _full_decision(f"{PREFIX}_E1", f"{PREFIX}_DECE1")
		frappe.get_doc(
			{
				"doctype": CA,
				"complaint": d.complaint,
				"decision": d.name,
				"action_type": "Notification",
				"status": "Planned",
			}
		).insert(ignore_permissions=True)
		execute_complaint_decision(d.name, actor_user="Administrator")
		self.assertEqual(int(frappe.db.get_value(CD, d.name, "decision_locked") or 0), 1)
		open_actions = frappe.get_all(CA, filters={"decision": d.name, "status": ("!=", "Completed")})
		self.assertEqual(len(open_actions), 0)

	def test_KT_GOV024_execute_requires_open_actions(self):
		d = _full_decision(f"{PREFIX}_E2", f"{PREFIX}_DECE2")
		self.assertRaises(frappe.ValidationError, execute_complaint_decision, d.name)
