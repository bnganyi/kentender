# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-007: Follow Up Action."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from kentender.tests.test_procuring_entity import run_test_db_cleanup

from kentender_governance.tests.gov_test_utils import cleanup_gov_chain, make_deliberation_session, make_procuring_entity

PREFIX = "_KT_GOV007"
FUA = "Follow Up Action"
RES = "Resolution Record"
DAI = "Deliberation Agenda Item"


class TestFollowUpAction007(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(lambda: cleanup_gov_chain(PREFIX))
		self.pe = make_procuring_entity(f"{PREFIX}_PE")
		self.session = make_deliberation_session(
			business_id=f"{PREFIX}_S1", procuring_entity=self.pe.name
		)
		self.agenda = frappe.get_doc(
			{
				"doctype": DAI,
				"deliberation_session": self.session,
				"item_no": 1,
				"title": "Topic",
				"status": "Open",
			}
		).insert(ignore_permissions=True)
		self.resolution = frappe.get_doc(
			{
				"doctype": RES,
				"deliberation_session": self.session,
				"agenda_item": self.agenda.name,
				"resolution_text": "Action required.",
				"resolution_date": today(),
				"effective_status": "Effective",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(lambda: cleanup_gov_chain(PREFIX))
		super().tearDown()

	def test_KT_GOV007_valid_create_and_complete(self):
		doc = frappe.get_doc(
			{
				"doctype": FUA,
				"deliberation_session": self.session,
				"resolution_record": self.resolution.name,
				"action_title": "Send notice",
				"assigned_to_user": "Administrator",
				"due_date": add_days(today(), 7),
				"status": "Open",
			}
		).insert(ignore_permissions=True)
		doc.status = "Completed"
		doc.completion_notes = "Done."
		doc.save(ignore_permissions=True)
		self.assertEqual(doc.status, "Completed")

	def test_KT_GOV007_resolution_other_session_blocked(self):
		other_sess = make_deliberation_session(business_id=f"{PREFIX}_S2", procuring_entity=self.pe.name)
		ag2 = frappe.get_doc(
			{
				"doctype": DAI,
				"deliberation_session": other_sess,
				"item_no": 1,
				"title": "T2",
				"status": "Open",
			}
		).insert(ignore_permissions=True)
		res2 = frappe.get_doc(
			{
				"doctype": RES,
				"deliberation_session": other_sess,
				"agenda_item": ag2.name,
				"resolution_text": "Other",
				"resolution_date": today(),
				"effective_status": "Draft",
			}
		).insert(ignore_permissions=True)
		row = {
			"doctype": FUA,
			"deliberation_session": self.session,
			"resolution_record": res2.name,
			"action_title": "Bad link",
			"assigned_to_user": "Administrator",
			"due_date": today(),
			"status": "Open",
		}
		self.assertRaises(frappe.ValidationError, frappe.get_doc(row).insert, ignore_permissions=True)
		frappe.delete_doc(RES, res2.name, force=True, ignore_permissions=True)
		frappe.delete_doc(DAI, ag2.name, force=True, ignore_permissions=True)
		frappe.delete_doc("Deliberation Session", other_sess, force=True, ignore_permissions=True)
