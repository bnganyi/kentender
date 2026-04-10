# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-023: complaint review panel, review submission, decision issuance."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import run_test_db_cleanup

from kentender_governance.services.complaint_intake_services import review_complaint_admissibility, submit_complaint
from kentender_governance.services.complaint_review_services import (
	assign_complaint_reviewer,
	issue_complaint_decision,
	submit_complaint_review,
)
from kentender_governance.tests.gov_test_utils import cleanup_complaint_chain

PREFIX = "_KT_GOV023"
CD = "Complaint Decision"
CSE = "Complaint Status Event"


def _intake_admissible(business_id: str):
	doc = submit_complaint(
		business_id=business_id,
		complaint_title="Review flow",
		complaint_type="Other",
		complainant_type="Citizen",
		complainant_name="B",
		complaint_summary="S",
		complaint_details="<p>D</p>",
		requested_remedy="R",
		received_by_user="Administrator",
		complainant_contact_email="b@example.com",
	)
	review_complaint_admissibility(
		doc.name,
		"Admissible",
		admissibility_reason="OK",
		reviewed_by_user="Administrator",
	)
	return doc.name


class TestComplaintReviewServices023(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(lambda: cleanup_complaint_chain(PREFIX))

	def tearDown(self):
		run_test_db_cleanup(lambda: cleanup_complaint_chain(PREFIX))
		super().tearDown()

	def test_KT_GOV023_assign_review_issue_decision(self):
		cid = _intake_admissible(f"{PREFIX}_R1")
		assign_complaint_reviewer(cid, "Administrator", role_type="Chair", actor_user="Administrator")
		submit_complaint_review(
			cid,
			review_summary="Looks valid",
			recommended_outcome="Dismiss",
			reviewer_user="Administrator",
			actor_user="Administrator",
		)
		d = issue_complaint_decision(
			cid,
			decision_business_id=f"{PREFIX}_DEC",
			decision_result="Dismissed",
			decision_summary="No breach",
			decided_by_user="Administrator",
			actor_user="Administrator",
		)
		self.assertEqual(d.status, "Final")
		self.assertTrue(frappe.db.exists(CD, d.name))
		ev = frappe.get_all(CSE, filters={"complaint": cid}, pluck="event_type", order_by="creation asc")
		self.assertIn("PanelAssigned", ev)
		self.assertIn("ReviewSubmitted", ev)
		self.assertIn("Decided", ev)

	def test_KT_GOV023_review_requires_panel_assignment(self):
		cid = _intake_admissible(f"{PREFIX}_R2")
		self.assertRaises(
			frappe.ValidationError,
			submit_complaint_review,
			cid,
			"Summary",
			"Outcome",
			reviewer_user="Administrator",
		)

	def test_KT_GOV023_decision_requires_submitted_review(self):
		cid = _intake_admissible(f"{PREFIX}_R3")
		assign_complaint_reviewer(cid, "Administrator", actor_user="Administrator")
		self.assertRaises(
			frappe.ValidationError,
			issue_complaint_decision,
			cid,
			f"{PREFIX}_DEC2",
			"Rejected",
			"Nope",
			"Administrator",
		)
