# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-100: Inspection Method Template."""

import frappe
from frappe.model.base_document import get_controller
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import run_test_db_cleanup

IMT = "Inspection Method Template"
PREFIX = "_KT_INSP100"


def _cleanup_insp100():
	for name in frappe.get_all(IMT, filters={"name": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(IMT, name, force=True, ignore_permissions=True)


def _template_kwargs(template_code: str, **extra):
	kw = {
		"doctype": IMT,
		"template_code": template_code,
		"template_name": "Test inspection template",
		"inspection_domain": "General",
		"applicable_contract_type": "Goods",
		"inspection_method_type": "Checklist",
		"default_pass_logic": "All Mandatory Pass",
	}
	kw.update(extra)
	return kw


class TestInspectionMethodTemplate100(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(_cleanup_insp100)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_insp100)
		super().tearDown()

	def test_KT_INSP100_valid_create(self):
		code = f"{PREFIX}_001"
		doc = frappe.get_doc(_template_kwargs(code))
		doc.insert(ignore_permissions=True)
		self.assertEqual(doc.name, code)
		self.assertEqual(doc.display_label, f"{code} — Test inspection template")
		doc.reload()
		self.assertEqual(doc.display_label, f"{code} — Test inspection template")

	def test_KT_INSP100_duplicate_template_code_blocked(self):
		code = f"{PREFIX}_DUP"
		frappe.get_doc(_template_kwargs(code)).insert(ignore_permissions=True)
		dup = frappe.get_doc(_template_kwargs(code, template_name="Another name"))
		self.assertRaises(frappe.DuplicateEntryError, dup.insert, ignore_permissions=True)

	def test_KT_INSP100_controller_import(self):
		cls = get_controller(IMT)
		self.assertEqual(cls.__name__, "InspectionMethodTemplate")
