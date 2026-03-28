# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity


def _make_department(
	department_code: str,
	procuring_entity: str,
	**kwargs,
):
	doc = frappe.get_doc(
		{
			"doctype": "Procuring Department",
			"department_code": department_code,
			"department_name": kwargs.pop("department_name", f"Dept {department_code}"),
			"procuring_entity": procuring_entity,
			**kwargs,
		}
	)
	return doc


class TestProcuringDepartment(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()

	def tearDown(self):
		frappe.db.delete(
			"Procuring Department",
			{"department_code": ("like", "_KT_PD_%")},
		)
		frappe.db.delete(
			"Procuring Entity",
			{"entity_code": ("like", "_KT_PE_PD%")},
		)
		frappe.db.commit()
		super().tearDown()

	def test_valid_create(self):
		ent = _make_entity("_KT_PE_PD1")
		ent.insert()
		doc = _make_department("_KT_PD_HR", ent.name)
		doc.insert()
		self.assertEqual(doc.name, f"_KT_PD_HR-{ent.name}")
		self.assertFalse(doc.parent_department)

	def test_duplicate_department_code_same_entity_blocked(self):
		ent = _make_entity("_KT_PE_PD2")
		ent.insert()
		_make_department("_KT_PD_FIN", ent.name).insert()
		dup = _make_department("_KT_PD_FIN", ent.name)
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)

	def test_same_department_code_different_entities_allowed(self):
		a = _make_entity("_KT_PE_PDA")
		a.insert()
		b = _make_entity("_KT_PE_PDB")
		b.insert()
		d1 = _make_department("_KT_PD_SHARED", a.name)
		d1.insert()
		d2 = _make_department("_KT_PD_SHARED", b.name)
		d2.insert()
		self.assertNotEqual(d1.name, d2.name)

	def test_parent_must_match_procuring_entity(self):
		ent_a = _make_entity("_KT_PE_PDC")
		ent_a.insert()
		ent_b = _make_entity("_KT_PE_PDD")
		ent_b.insert()
		parent = _make_department("_KT_PD_PARENT", ent_a.name)
		parent.insert()
		child = _make_department("_KT_PD_CHILD", ent_b.name, parent_department=parent.name)
		self.assertRaises(frappe.ValidationError, child.insert)

	def test_self_parent_blocked(self):
		ent = _make_entity("_KT_PE_PDE")
		ent.insert()
		doc = _make_department("_KT_PD_SELF", ent.name)
		doc.insert()
		doc.parent_department = doc.name
		self.assertRaises(frappe.ValidationError, doc.save)

	def test_circular_hierarchy_blocked(self):
		ent = _make_entity("_KT_PE_PDF")
		ent.insert()
		root = _make_department("_KT_PD_ROOT", ent.name)
		root.insert()
		child = _make_department("_KT_PD_CHILD2", ent.name, parent_department=root.name)
		child.insert()
		root.parent_department = child.name
		self.assertRaises(frappe.ValidationError, root.save)
