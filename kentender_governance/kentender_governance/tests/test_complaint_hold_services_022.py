# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-022: complaint procurement hold services."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import run_test_db_cleanup

from kentender_governance.services.complaint_hold_services import apply_procurement_hold, release_procurement_hold
from kentender_governance.services.complaint_intake_services import review_complaint_admissibility, submit_complaint
from kentender_governance.tests.gov_test_utils import cleanup_complaint_chain

PREFIX = "_KT_GOV022"
C = "Complaint"
CSE = "Complaint Status Event"


def _submit_admissible(business_id: str):
	doc = submit_complaint(
		business_id=business_id,
		complaint_title="Hold test",
		complaint_type="Other",
		complainant_type="Citizen",
		complainant_name="A",
		complaint_summary="S",
		complaint_details="<p>D</p>",
		requested_remedy="R",
		received_by_user="Administrator",
		complainant_contact_email="a@example.com",
	)
	review_complaint_admissibility(
		doc.name,
		"Admissible",
		admissibility_reason="OK",
		reviewed_by_user="Administrator",
	)
	return doc.name


class TestComplaintHoldServices022(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(lambda: cleanup_complaint_chain(PREFIX))

	def tearDown(self):
		run_test_db_cleanup(lambda: cleanup_complaint_chain(PREFIX))
		super().tearDown()

	def test_KT_GOV022_apply_and_release_hold(self):
		cid = _submit_admissible(f"{PREFIX}_H1")
		apply_procurement_hold(
			cid,
			affects_award_process=1,
			affects_contract_execution=0,
			hold_scope="Award signing",
			actor_user="Administrator",
		)
		self.assertEqual(frappe.db.get_value(C, cid, "hold_status"), "Active")
		self.assertEqual(int(frappe.db.get_value(C, cid, "affects_award_process") or 0), 1)
		release_procurement_hold(cid, actor_user="Administrator")
		self.assertEqual(frappe.db.get_value(C, cid, "hold_status"), "Released")

	def test_KT_GOV022_hold_blocked_before_review_phase(self):
		doc = submit_complaint(
			business_id=f"{PREFIX}_H2",
			complaint_title="Hold test",
			complaint_type="Other",
			complainant_type="Citizen",
			complainant_name="A",
			complaint_summary="S",
			complaint_details="<p>D</p>",
			requested_remedy="R",
			received_by_user="Administrator",
			complainant_contact_email="a@example.com",
		)
		self.assertRaises(frappe.ValidationError, apply_procurement_hold, doc.name)

	def test_KT_GOV022_events_on_apply(self):
		cid = _submit_admissible(f"{PREFIX}_H3")
		apply_procurement_hold(cid, affects_award_process=1, actor_user="Administrator")
		ev = frappe.get_all(CSE, filters={"complaint": cid}, pluck="event_type", order_by="creation asc")
		self.assertIn("Other", ev)
