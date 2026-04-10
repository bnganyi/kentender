# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-004: Deliberation Minute."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime

from kentender.tests.test_procuring_entity import run_test_db_cleanup

from kentender_governance.tests.gov_test_utils import cleanup_gov_chain, make_deliberation_session, make_procuring_entity

PREFIX = "_KT_GOV004"
DM = "Deliberation Minute"
DAI = "Deliberation Agenda Item"


class TestDeliberationMinute004(FrappeTestCase):
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
				"title": "Item 1",
				"status": "Open",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(lambda: cleanup_gov_chain(PREFIX))
		super().tearDown()

	def test_KT_GOV004_valid_draft_and_finalized(self):
		d = frappe.get_doc(
			{
				"doctype": DM,
				"deliberation_session": self.session,
				"agenda_item": self.agenda.name,
				"minute_text": "Discussion noted.",
				"recorded_by_user": "Administrator",
				"recorded_on": now_datetime(),
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(d.status, "Draft")
		d.status = "Finalized"
		d.save(ignore_permissions=True)
		self.assertEqual(d.status, "Finalized")

	def test_KT_GOV004_agenda_wrong_session_blocked(self):
		other = make_deliberation_session(business_id=f"{PREFIX}_S2", procuring_entity=self.pe.name)
		other_ag = frappe.get_doc(
			{
				"doctype": DAI,
				"deliberation_session": other,
				"item_no": 1,
				"title": "Other",
				"status": "Open",
			}
		).insert(ignore_permissions=True)
		row = {
			"doctype": DM,
			"deliberation_session": self.session,
			"agenda_item": other_ag.name,
			"minute_text": "x",
			"recorded_by_user": "Administrator",
			"recorded_on": now_datetime(),
			"status": "Draft",
		}
		self.assertRaises(frappe.ValidationError, frappe.get_doc(row).insert, ignore_permissions=True)
		frappe.delete_doc(DAI, other_ag.name, force=True, ignore_permissions=True)
		frappe.delete_doc("Deliberation Session", other, force=True, ignore_permissions=True)
