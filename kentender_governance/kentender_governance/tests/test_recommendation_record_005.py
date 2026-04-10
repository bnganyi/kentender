# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-005: Recommendation Record."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import run_test_db_cleanup

from kentender_governance.tests.gov_test_utils import cleanup_gov_chain, make_deliberation_session, make_procuring_entity

PREFIX = "_KT_GOV005"
RR = "Recommendation Record"
DAI = "Deliberation Agenda Item"


class TestRecommendationRecord005(FrappeTestCase):
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

	def test_KT_GOV005_valid_create(self):
		doc = frappe.get_doc(
			{
				"doctype": RR,
				"deliberation_session": self.session,
				"agenda_item": self.agenda.name,
				"recommendation_type": "Approve",
				"recommendation_text": "Proceed as planned.",
				"recommended_by_user": "Administrator",
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(doc.display_label)

	def test_KT_GOV005_invalid_related_document(self):
		row = {
			"doctype": RR,
			"deliberation_session": self.session,
			"agenda_item": self.agenda.name,
			"recommendation_type": "Refer",
			"recommendation_text": "See ref",
			"related_doctype": "User",
			"related_docname": "missing_user_gov005",
			"recommended_by_user": "Administrator",
			"status": "Draft",
		}
		self.assertRaises(frappe.ValidationError, frappe.get_doc(row).insert, ignore_permissions=True)
