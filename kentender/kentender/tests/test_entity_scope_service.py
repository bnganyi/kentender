# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.services.entity_scope_service import (
	get_record_entity_value,
	is_central_entity_scope_user,
	record_belongs_to_entity,
	user_has_entity_access,
	user_may_access_scoped_record,
)
from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

_ROLE = "KT C008 Scope Test"
_USER = "kt_c008_scope@test.com"
_ENTITY_A = "_KT_C008_A"
_ENTITY_B = "_KT_C008_B"


def _ensure_test_role():
	if not frappe.db.exists("Role", _ROLE):
		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": _ROLE,
				"desk_access": 1,
			}
		).insert(ignore_permissions=True)


def _ensure_scoped_user():
	_ensure_test_role()
	if frappe.db.exists("User", _USER):
		return
	doc = frappe.get_doc(
		{
			"doctype": "User",
			"email": _USER,
			"first_name": "Scope",
			"send_welcome_email": 0,
			"enabled": 1,
		}
	)
	doc.append("roles", {"role": _ROLE})
	doc.insert(ignore_permissions=True)


class TestEntityScopeService(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		self.a = _make_entity(_ENTITY_A)
		self.a.insert()
		self.b = _make_entity(_ENTITY_B)
		self.b.insert()

	def tearDown(self):
		frappe.db.delete("User Permission", {"user": _USER})
		if frappe.db.exists("User", _USER):
			frappe.delete_doc("User", _USER, force=1, ignore_permissions=1)
		frappe.db.delete("Exception Record", {"business_id": ("like", "_KT_C008_EX%")})
		frappe.db.delete("Procuring Department", {"department_code": ("like", "_KT_C008_DP%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_C008_%")})
		frappe.db.commit()
		super().tearDown()

	def test_get_record_entity_value(self):
		self.assertEqual(
			get_record_entity_value({"procuring_entity": self.a.name}),
			self.a.name,
		)
		self.assertIsNone(get_record_entity_value({}))

	def test_record_belongs_procuring_entity_doc(self):
		self.assertTrue(record_belongs_to_entity(self.a, self.a.name))
		self.assertFalse(record_belongs_to_entity(self.a, self.b.name))

	def test_record_belongs_exception_record(self):
		ex = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"business_id": "_KT_C008_EX1",
				"exception_type": "Other",
				"procuring_entity": self.a.name,
				"triggered_by": "Administrator",
				"justification": "Justification long enough for validation rules here.",
			}
		)
		ex.insert()
		self.assertTrue(record_belongs_to_entity(ex, self.a.name))
		self.assertFalse(record_belongs_to_entity(ex, self.b.name))

	def test_record_belongs_procuring_department(self):
		dept = frappe.get_doc(
			{
				"doctype": "Procuring Department",
				"department_code": "_KT_C008_DP1",
				"department_name": "Test Dept",
				"procuring_entity": self.a.name,
			}
		)
		dept.insert()
		self.assertTrue(record_belongs_to_entity(dept, self.a.name))
		self.assertFalse(record_belongs_to_entity(dept, self.b.name))

	def test_is_central_entity_scope_user(self):
		self.assertTrue(is_central_entity_scope_user("Administrator"))
		self.assertTrue(is_central_entity_scope_user(None))

	def test_user_has_entity_access_central(self):
		self.assertTrue(
			user_has_entity_access("Administrator", self.a.name, allow_central=True),
		)

	def test_user_has_entity_access_via_user_permission(self):
		_ensure_scoped_user()
		self.assertFalse(user_has_entity_access(_USER, self.a.name, allow_central=False))
		frappe.get_doc(
			{
				"doctype": "User Permission",
				"user": _USER,
				"allow": "Procuring Entity",
				"for_value": self.a.name,
			}
		).insert(ignore_permissions=True)
		self.assertTrue(user_has_entity_access(_USER, self.a.name, allow_central=False))
		self.assertFalse(user_has_entity_access(_USER, self.b.name, allow_central=False))

	def test_user_may_access_scoped_record_central_bypass(self):
		ex = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"business_id": "_KT_C008_EX2",
				"exception_type": "Other",
				"procuring_entity": self.b.name,
				"triggered_by": "Administrator",
				"justification": "Justification long enough for validation rules here.",
			}
		)
		ex.insert()
		self.assertTrue(
			user_may_access_scoped_record(
				"Administrator",
				ex,
				active_entity=self.a.name,
				allow_central=True,
			),
		)

	def test_user_may_access_scoped_record_scoped_user_positive(self):
		_ensure_scoped_user()
		frappe.get_doc(
			{
				"doctype": "User Permission",
				"user": _USER,
				"allow": "Procuring Entity",
				"for_value": self.a.name,
			}
		).insert(ignore_permissions=True)
		ex = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"business_id": "_KT_C008_EX3",
				"exception_type": "Other",
				"procuring_entity": self.a.name,
				"triggered_by": "Administrator",
				"justification": "Justification long enough for validation rules here.",
			}
		)
		ex.insert()
		self.assertTrue(
			user_may_access_scoped_record(
				_USER,
				ex,
				active_entity=self.a.name,
				allow_central=True,
			),
		)

	def test_user_may_access_scoped_record_wrong_active_entity(self):
		_ensure_scoped_user()
		frappe.get_doc(
			{
				"doctype": "User Permission",
				"user": _USER,
				"allow": "Procuring Entity",
				"for_value": self.a.name,
			}
		).insert(ignore_permissions=True)
		ex = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"business_id": "_KT_C008_EX4",
				"exception_type": "Other",
				"procuring_entity": self.a.name,
				"triggered_by": "Administrator",
				"justification": "Justification long enough for validation rules here.",
			}
		)
		ex.insert()
		self.assertFalse(
			user_may_access_scoped_record(
				_USER,
				ex,
				active_entity=self.b.name,
				allow_central=True,
			),
		)

	def test_user_may_access_scoped_record_non_central_no_active_entity(self):
		_ensure_scoped_user()
		ex = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"business_id": "_KT_C008_EX5",
				"exception_type": "Other",
				"procuring_entity": self.a.name,
				"triggered_by": "Administrator",
				"justification": "Justification long enough for validation rules here.",
			}
		)
		ex.insert()
		self.assertFalse(
			user_may_access_scoped_record(
				_USER,
				ex,
				active_entity=None,
				allow_central=True,
			),
		)
