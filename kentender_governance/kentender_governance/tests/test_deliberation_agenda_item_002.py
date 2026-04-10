# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-002: Deliberation Agenda Item."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import run_test_db_cleanup

from kentender_governance.tests.gov_test_utils import cleanup_gov_chain, make_deliberation_session, make_procuring_entity

PREFIX = "_KT_GOV002"
DAI = "Deliberation Agenda Item"


class TestDeliberationAgendaItem002(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(lambda: cleanup_gov_chain(PREFIX))
		self.pe = make_procuring_entity(f"{PREFIX}_PE")
		self.session = make_deliberation_session(
			business_id=f"{PREFIX}_S1", procuring_entity=self.pe.name
		)

	def tearDown(self):
		run_test_db_cleanup(lambda: cleanup_gov_chain(PREFIX))
		super().tearDown()

	def _row(self, suf: str, item_no: int = 1, **extra):
		return {
			"doctype": DAI,
			"deliberation_session": self.session,
			"item_no": item_no,
			"title": f"Agenda {suf}",
			"status": "Open",
			**extra,
		}

	def test_KT_GOV002_valid_create_and_order(self):
		a = frappe.get_doc(self._row("A", item_no=1)).insert(ignore_permissions=True)
		b = frappe.get_doc(self._row("B", item_no=2)).insert(ignore_permissions=True)
		self.assertTrue(a.display_label)
		self.assertNotEqual(a.name, b.name)

	def test_KT_GOV002_duplicate_item_no_blocked(self):
		frappe.get_doc(self._row("X", item_no=5)).insert(ignore_permissions=True)
		dup = frappe.get_doc(self._row("Y", item_no=5))
		self.assertRaises(frappe.ValidationError, dup.insert, ignore_permissions=True)

	def test_KT_GOV002_invalid_linked_document(self):
		row = self._row("LINK", item_no=3)
		row["linked_doctype"] = "User"
		row["linked_docname"] = "nonexistent_user_xyz_999"
		self.assertRaises(frappe.ValidationError, frappe.get_doc(row).insert, ignore_permissions=True)
