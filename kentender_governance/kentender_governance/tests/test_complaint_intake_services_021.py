# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-021: complaint intake and admissibility services."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import run_test_db_cleanup

from kentender_governance.services.complaint_intake_services import (
	review_complaint_admissibility,
	submit_complaint,
	withdraw_complaint,
)
from kentender_governance.tests.gov_test_utils import cleanup_complaint_chain

PREFIX = "_KT_GOV021"
C = "Complaint"
CSE = "Complaint Status Event"


def _base_submit_kwargs(business_id: str):
	return {
		"business_id": business_id,
		"complaint_title": "Procurement concern",
		"complaint_type": "Other",
		"complainant_type": "Citizen",
		"complainant_name": "Test User",
		"complaint_summary": "Summary text",
		"complaint_details": "<p>Structured details</p>",
		"requested_remedy": "Fair review",
		"received_by_user": "Administrator",
		"complainant_contact_email": "user@example.com",
	}


class TestComplaintIntakeServices021(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(lambda: cleanup_complaint_chain(PREFIX))

	def tearDown(self):
		run_test_db_cleanup(lambda: cleanup_complaint_chain(PREFIX))
		super().tearDown()

	def _events(self, complaint: str):
		return frappe.get_all(
			CSE,
			filters={"complaint": complaint},
			fields=["event_type", "summary"],
			order_by="creation asc",
		)

	def test_KT_GOV021_submit_emits_submitted_event(self):
		doc = submit_complaint(**_base_submit_kwargs(f"{PREFIX}_S1"), actor_user="Administrator")
		self.assertEqual(doc.status, "Submitted")
		self.assertEqual(doc.workflow_state, "Admissibility")
		self.assertEqual(doc.admissibility_status, "Pending")
		ev = self._events(doc.name)
		self.assertEqual(len(ev), 1)
		self.assertEqual(ev[0].event_type, "Submitted")

	def test_KT_GOV021_review_admissible(self):
		doc = submit_complaint(**_base_submit_kwargs(f"{PREFIX}_A1"))
		review_complaint_admissibility(
			doc.name,
			"Admissible",
			admissibility_reason="Meets criteria",
			reviewed_by_user="Administrator",
		)
		self.assertEqual(frappe.db.get_value(C, doc.name, "admissibility_status"), "Admissible")
		self.assertEqual(frappe.db.get_value(C, doc.name, "status"), "Under Review")
		self.assertEqual(frappe.db.get_value(C, doc.name, "workflow_state"), "Panel Review")
		types = [r.event_type for r in self._events(doc.name)]
		self.assertEqual(types, ["Submitted", "AdmissibilityReviewed"])

	def test_KT_GOV021_review_inadmissible_closes(self):
		doc = submit_complaint(**_base_submit_kwargs(f"{PREFIX}_I1"))
		review_complaint_admissibility(
			doc.name,
			"Inadmissible",
			admissibility_reason="Outside jurisdiction",
			reviewed_by_user="Administrator",
		)
		self.assertEqual(frappe.db.get_value(C, doc.name, "status"), "Closed")
		self.assertEqual(frappe.db.get_value(C, doc.name, "workflow_state"), "Closed")

	def test_KT_GOV021_review_deferred_requires_reason(self):
		doc = submit_complaint(**_base_submit_kwargs(f"{PREFIX}_D0"))
		self.assertRaises(
			frappe.ValidationError,
			review_complaint_admissibility,
			doc.name,
			"Deferred",
			admissibility_reason="",
			reviewed_by_user="Administrator",
		)

	def test_KT_GOV021_deferred_then_admissible(self):
		doc = submit_complaint(**_base_submit_kwargs(f"{PREFIX}_D1"))
		review_complaint_admissibility(
			doc.name,
			"Deferred",
			admissibility_reason="Awaiting documents",
			reviewed_by_user="Administrator",
		)
		self.assertEqual(frappe.db.get_value(C, doc.name, "admissibility_status"), "Deferred")
		review_complaint_admissibility(
			doc.name,
			"Admissible",
			admissibility_reason="Documents received",
			reviewed_by_user="Administrator",
		)
		self.assertEqual(frappe.db.get_value(C, doc.name, "status"), "Under Review")

	def test_KT_GOV021_withdraw_after_submit(self):
		doc = submit_complaint(**_base_submit_kwargs(f"{PREFIX}_W1"))
		withdraw_complaint(doc.name, reason="Complainant retracted", actor_user="Administrator")
		self.assertEqual(frappe.db.get_value(C, doc.name, "status"), "Withdrawn")
		types = [r.event_type for r in self._events(doc.name)]
		self.assertEqual(types, ["Submitted", "Closed"])

	def test_KT_GOV021_duplicate_business_id(self):
		submit_complaint(**_base_submit_kwargs(f"{PREFIX}_DUP"))
		self.assertRaises(
			frappe.DuplicateEntryError,
			submit_complaint,
			**_base_submit_kwargs(f"{PREFIX}_DUP"),
		)

	def test_KT_GOV021_review_blocked_after_admissible(self):
		doc = submit_complaint(**_base_submit_kwargs(f"{PREFIX}_B1"))
		review_complaint_admissibility(
			doc.name,
			"Admissible",
			admissibility_reason="OK",
			reviewed_by_user="Administrator",
		)
		self.assertRaises(
			frappe.ValidationError,
			review_complaint_admissibility,
			doc.name,
			"Inadmissible",
			admissibility_reason="Too late",
			reviewed_by_user="Administrator",
		)

	def test_KT_GOV021_locked_blocks_review(self):
		doc = submit_complaint(**_base_submit_kwargs(f"{PREFIX}_L1"))
		frappe.db.set_value(C, doc.name, "complaint_locked", 1)
		self.assertRaises(
			frappe.ValidationError,
			review_complaint_admissibility,
			doc.name,
			"Admissible",
			admissibility_reason="x",
			reviewed_by_user="Administrator",
		)
