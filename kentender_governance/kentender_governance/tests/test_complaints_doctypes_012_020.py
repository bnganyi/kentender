# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-012–020: Complaints & Disputes DocTypes."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime

from kentender.tests.test_procuring_entity import run_test_db_cleanup

from kentender_governance.tests.gov_test_utils import cleanup_complaint_chain

PREFIX = "_KT_GOV012_020"
CMP = "Complaint"
CP = "Complaint Party"
CE = "Complaint Evidence"
CRPA = "Complaint Review Panel Assignment"
CRR = "Complaint Review Record"
CD = "Complaint Decision"
CA = "Complaint Action"
AR = "Appeal Record"
CSE = "Complaint Status Event"


def _complaint_payload(*, business_id: str):
	dt = now_datetime()
	return {
		"doctype": CMP,
		"business_id": business_id,
		"complaint_title": "Test complaint",
		"status": "Draft",
		"workflow_state": "Intake",
		"complaint_type": "Other",
		"complaint_stage": "Intake",
		"complainant_type": "Citizen",
		"complainant_name": "Jane Doe",
		"complainant_contact_email": "jane@example.com",
		"complaint_summary": "Summary",
		"complaint_details": "<p>Details</p>",
		"requested_remedy": "Review",
		"submission_datetime": dt,
		"received_by_user": "Administrator",
		"admissibility_status": "Pending",
	}


class TestComplaintsDoctypes012020(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(lambda: cleanup_complaint_chain(PREFIX))

	def tearDown(self):
		run_test_db_cleanup(lambda: cleanup_complaint_chain(PREFIX))
		super().tearDown()

	def test_KT_GOV012_create_and_display_label(self):
		doc = frappe.get_doc(_complaint_payload(business_id=f"{PREFIX}_C1")).insert(ignore_permissions=True)
		self.assertTrue(doc.display_label)
		self.assertEqual(doc.name, f"{PREFIX}_C1")

	def test_KT_GOV012_duplicate_business_id(self):
		frappe.get_doc(_complaint_payload(business_id=f"{PREFIX}_DUP")).insert(ignore_permissions=True)
		self.assertRaises(
			frappe.DuplicateEntryError,
			lambda: frappe.get_doc(_complaint_payload(business_id=f"{PREFIX}_DUP")).insert(ignore_permissions=True),
		)

	def test_KT_GOV012_invalid_email(self):
		p = _complaint_payload(business_id=f"{PREFIX}_BADEMAIL")
		p["complainant_contact_email"] = "not-an-email"
		self.assertRaises(frappe.ValidationError, lambda: frappe.get_doc(p).insert(ignore_permissions=True))

	def test_KT_GOV013_complaint_party(self):
		cid = frappe.get_doc(_complaint_payload(business_id=f"{PREFIX}_C13")).insert(ignore_permissions=True).name
		p = frappe.get_doc(
			{
				"doctype": CP,
				"complaint": cid,
				"party_role": "Complainant",
				"party_name": "Alpha",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(p.display_label)

	def test_KT_GOV014_evidence_with_party(self):
		cid = frappe.get_doc(_complaint_payload(business_id=f"{PREFIX}_C14")).insert(ignore_permissions=True).name
		pid = (
			frappe.get_doc(
				{
					"doctype": CP,
					"complaint": cid,
					"party_role": "Witness",
					"party_name": "Beta",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)
		ev = frappe.get_doc(
			{
				"doctype": CE,
				"complaint": cid,
				"submitted_by_party": pid,
				"evidence_type": "Document",
				"description": "Annex A",
				"submitted_on": now_datetime(),
				"sensitivity_class": "Internal",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(ev.display_label)

	def test_KT_GOV015_panel_assignment(self):
		cid = frappe.get_doc(_complaint_payload(business_id=f"{PREFIX}_C15")).insert(ignore_permissions=True).name
		a = frappe.get_doc(
			{
				"doctype": CRPA,
				"complaint": cid,
				"user": "Administrator",
				"role_type": "Chair",
				"assigned_on": now_datetime(),
			}
		).insert(ignore_permissions=True)
		self.assertTrue(a.display_label)

	def test_KT_GOV016_review_record(self):
		cid = frappe.get_doc(_complaint_payload(business_id=f"{PREFIX}_C16")).insert(ignore_permissions=True).name
		r = frappe.get_doc(
			{
				"doctype": CRR,
				"complaint": cid,
				"reviewer_user": "Administrator",
				"review_summary": "Looks consistent",
				"recommended_outcome": "Dismiss",
				"submitted_on": now_datetime(),
			}
		).insert(ignore_permissions=True)
		self.assertTrue(r.display_label)

	def test_KT_GOV017_complaint_decision(self):
		cid = frappe.get_doc(_complaint_payload(business_id=f"{PREFIX}_C17")).insert(ignore_permissions=True).name
		d = frappe.get_doc(
			{
				"doctype": CD,
				"business_id": f"{PREFIX}_DEC1",
				"complaint": cid,
				"decision_datetime": now_datetime(),
				"decided_by_user": "Administrator",
				"decision_result": "Dismissed",
				"decision_summary": "No breach",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(d.display_label)

	def test_KT_GOV018_action_targets_user_and_rejects_mismatched_decision(self):
		c1 = frappe.get_doc(_complaint_payload(business_id=f"{PREFIX}_C18A")).insert(ignore_permissions=True).name
		c2 = frappe.get_doc(_complaint_payload(business_id=f"{PREFIX}_C18B")).insert(ignore_permissions=True).name
		dec = frappe.get_doc(
			{
				"doctype": CD,
				"business_id": f"{PREFIX}_DEC18",
				"complaint": c1,
				"decision_datetime": now_datetime(),
				"decided_by_user": "Administrator",
				"decision_result": "Rejected",
				"decision_summary": "Out of scope",
			}
		).insert(ignore_permissions=True)
		act = frappe.get_doc(
			{
				"doctype": CA,
				"complaint": c1,
				"decision": dec.name,
				"action_type": "Notification",
				"target_doctype": "User",
				"target_docname": "Administrator",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(act.display_label)

		self.assertRaises(
			frappe.ValidationError,
			lambda: frappe.get_doc(
				{
					"doctype": CA,
					"complaint": c2,
					"decision": dec.name,
					"action_type": "Other",
				}
			).insert(ignore_permissions=True),
		)

	def test_KT_GOV019_appeal_record(self):
		cid = frappe.get_doc(_complaint_payload(business_id=f"{PREFIX}_C19")).insert(ignore_permissions=True).name
		dec = frappe.get_doc(
			{
				"doctype": CD,
				"business_id": f"{PREFIX}_DEC19",
				"complaint": cid,
				"decision_datetime": now_datetime(),
				"decided_by_user": "Administrator",
				"decision_result": "Rejected",
				"decision_summary": "Original decision",
			}
		).insert(ignore_permissions=True)
		ap = frappe.get_doc(
			{
				"doctype": AR,
				"complaint": cid,
				"complaint_decision": dec.name,
				"appeal_submitted_by": "Administrator",
				"appeal_summary": "We disagree",
				"appeal_details": "<p>Grounds</p>",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(ap.display_label)

	def test_KT_GOV020_status_event_append_only(self):
		cid = frappe.get_doc(_complaint_payload(business_id=f"{PREFIX}_C20")).insert(ignore_permissions=True).name
		ev = frappe.get_doc(
			{
				"doctype": CSE,
				"complaint": cid,
				"event_type": "Submitted",
				"event_datetime": now_datetime(),
				"actor_user": "Administrator",
				"summary": "Filed",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(ev.event_hash)
		ev.summary = "Changed"
		self.assertRaises(frappe.ValidationError, ev.save, ignore_permissions=True)
		self.assertRaises(frappe.ValidationError, frappe.delete_doc, CSE, ev.name, ignore_permissions=True)
