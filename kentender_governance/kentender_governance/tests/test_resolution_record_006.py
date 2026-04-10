# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-006: Resolution Record."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

from kentender.tests.test_procuring_entity import run_test_db_cleanup

from kentender_governance.tests.gov_test_utils import cleanup_gov_chain, make_deliberation_session, make_procuring_entity

PREFIX = "_KT_GOV006"
RES = "Resolution Record"
DAI = "Deliberation Agenda Item"


class TestResolutionRecord006(FrappeTestCase):
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

	def tearDown(self):
		run_test_db_cleanup(lambda: cleanup_gov_chain(PREFIX))
		super().tearDown()

	def test_KT_GOV006_valid_effective(self):
		doc = frappe.get_doc(
			{
				"doctype": RES,
				"deliberation_session": self.session,
				"agenda_item": self.agenda.name,
				"resolution_text": "Resolved unanimously.",
				"resolution_date": today(),
				"effective_status": "Effective",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(doc.effective_status, "Effective")
