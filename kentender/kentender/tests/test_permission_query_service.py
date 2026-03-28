# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.services.assignment_access_service import (
	ASSIGNMENT_DOCTYPE,
	list_assigned_target_docnames_for_user,
)
from kentender.services.permission_query_service import (
	merge_entity_scope_filters,
	name_in_docnames,
	or_filters_entity_or_docnames,
	owner_is_user,
)
from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

_ENTITY_A = "_KT_PQ_A"
_ENTITY_B = "_KT_PQ_B"
_USER = "kt_pq_user@test.com"
_ROLE = "KT PQ Test Role"


def _ensure_role():
	if not frappe.db.exists("Role", _ROLE):
		frappe.get_doc(
			{"doctype": "Role", "role_name": _ROLE, "desk_access": 1}
		).insert(ignore_permissions=True)


def _ensure_user():
	_ensure_role()
	if frappe.db.exists("User", _USER):
		return
	doc = frappe.get_doc(
		{
			"doctype": "User",
			"email": _USER,
			"first_name": "PQ",
			"send_welcome_email": 0,
			"enabled": 1,
		}
	)
	doc.append("roles", {"role": _ROLE})
	doc.insert(ignore_permissions=True)


class TestPermissionQueryFragments(FrappeTestCase):
	def test_owner_is_user(self):
		self.assertEqual(owner_is_user("Administrator"), {"owner": "Administrator"})
		self.assertEqual(
			owner_is_user("u@x.com", owner_field="triggered_by"),
			{"triggered_by": "u@x.com"},
		)

	def test_name_in_docnames(self):
		self.assertEqual(
			name_in_docnames(["a", "b"]),
			{"name": ("in", ["a", "b"])},
		)
		self.assertEqual(
			name_in_docnames([]),
			{"name": ("in", [])},
		)


class TestMergeEntityScopeFilters(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		_ensure_user()
		self.entity_a = _make_entity(_ENTITY_A)
		self.entity_a.insert()
		self.entity_b = _make_entity(_ENTITY_B)
		self.entity_b.insert()
		frappe.db.delete("User Permission", {"user": _USER})
		frappe.get_doc(
			{
				"doctype": "User Permission",
				"user": _USER,
				"allow": "Procuring Entity",
				"for_value": self.entity_a.name,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.db.delete("User Permission", {"user": _USER})
		if frappe.db.exists("User", _USER):
			frappe.delete_doc("User", _USER, force=1, ignore_permissions=1)
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_PQ_%")})
		frappe.db.commit()
		super().tearDown()

	def test_central_without_active_entity_adds_no_field(self):
		f = merge_entity_scope_filters(
			{"status": "Open"},
			"Administrator",
			allow_central=True,
			active_entity=None,
		)
		self.assertEqual(f, {"status": "Open"})
		self.assertNotIn("procuring_entity", f)

	def test_central_with_active_entity_restricts(self):
		f = merge_entity_scope_filters(
			{},
			"Administrator",
			allow_central=True,
			active_entity=self.entity_b.name,
		)
		self.assertEqual(f["procuring_entity"], self.entity_b.name)

	def test_scoped_user_single_entity_in_list_collapses_to_equals(self):
		f = merge_entity_scope_filters({}, _USER, allow_central=True, active_entity=None)
		self.assertEqual(f["procuring_entity"], self.entity_a.name)

	def test_scoped_user_active_entity_must_be_allowed(self):
		f = merge_entity_scope_filters(
			{},
			_USER,
			allow_central=True,
			active_entity=self.entity_b.name,
		)
		self.assertEqual(f.get("name"), ("in", []))

	def test_scoped_user_no_permissions_matches_nothing(self):
		frappe.db.delete("User Permission", {"user": _USER})
		f = merge_entity_scope_filters({}, _USER, allow_central=True, active_entity=None)
		self.assertEqual(f.get("name"), ("in", []))


class TestAssignmentQueryIntegration(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		_ensure_user()
		self.entity = _make_entity("_KT_PQ_E")
		self.entity.insert()
		self.ex1 = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"business_id": "_KT_PQ_EX1",
				"exception_type": "Other",
				"procuring_entity": self.entity.name,
				"triggered_by": "Administrator",
				"justification": "Permission query integration test justification.",
			}
		)
		self.ex1.insert()
		self.ex2 = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"business_id": "_KT_PQ_EX2",
				"exception_type": "Other",
				"procuring_entity": self.entity.name,
				"triggered_by": "Administrator",
				"justification": "Permission query integration test justification.",
			}
		)
		self.ex2.insert()
		frappe.get_doc(
			{
				"doctype": ASSIGNMENT_DOCTYPE,
				"assignment_type": "Committee",
				"user": _USER,
				"assignment_role": "Member",
				"target_doctype": "Exception Record",
				"target_docname": self.ex1.name,
				"active": 1,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.db.delete(ASSIGNMENT_DOCTYPE, {"target_docname": ("like", "_KT_PQ_EX%")})
		frappe.db.delete("Exception Record", {"business_id": ("like", "_KT_PQ_EX%")})
		if frappe.db.exists("User", _USER):
			frappe.delete_doc("User", _USER, force=1, ignore_permissions=1)
		frappe.db.delete("Procuring Entity", {"entity_code": "_KT_PQ_E"})
		frappe.db.commit()
		super().tearDown()

	def test_list_assigned_target_docnames_for_user(self):
		names = list_assigned_target_docnames_for_user(
			_USER,
			"Exception Record",
		)
		self.assertEqual(names, [self.ex1.name])

	def test_get_all_with_name_in_docnames(self):
		f = name_in_docnames(list_assigned_target_docnames_for_user(_USER, "Exception Record"))
		rows = frappe.get_all(
			"Exception Record",
			filters=f,
			pluck="name",
		)
		self.assertEqual(sorted(rows), [self.ex1.name])


class TestOrFiltersEntityOrDocnames(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		self.entity_a = _make_entity("_KT_PQ_OA")
		self.entity_a.insert()
		self.entity_b = _make_entity("_KT_PQ_OB")
		self.entity_b.insert()
		self.ex_a = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"business_id": "_KT_PQ_OX1",
				"exception_type": "Other",
				"procuring_entity": self.entity_a.name,
				"triggered_by": "Administrator",
				"justification": "OR filter test justification text here.",
			}
		)
		self.ex_a.insert()
		self.ex_b = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"business_id": "_KT_PQ_OX2",
				"exception_type": "Other",
				"procuring_entity": self.entity_b.name,
				"triggered_by": "Administrator",
				"justification": "OR filter test justification text here.",
			}
		)
		self.ex_b.insert()

	def tearDown(self):
		frappe.db.delete("Exception Record", {"business_id": ("like", "_KT_PQ_OX%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_PQ_O%")})
		frappe.db.commit()
		super().tearDown()

	def test_or_filters_union_entity_and_name(self):
		of = or_filters_entity_or_docnames(
			entity_field="procuring_entity",
			entity_values=[self.entity_a.name],
			docnames=[self.ex_b.name],
		)
		rows = frappe.get_all(
			"Exception Record",
			filters={"business_id": ("like", "_KT_PQ_OX%")},
			or_filters=of,
			pluck="name",
		)
		self.assertEqual(sorted(rows), sorted([self.ex_a.name, self.ex_b.name]))
