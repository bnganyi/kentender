# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate

from kentender.services.assignment_access_service import (
	ASSIGNMENT_DOCTYPE,
	assignment_valid_for_date,
	get_assignments_for_target,
	user_assignment_roles_on_target,
	user_has_assignment,
)
from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

_ENTITY = "_KT_ASG_PE"
_EX = "_KT_ASG_EX1"
_USER = "kt_asg_user@test.com"
_ROLE = "KT ASG Test Role"


def _ensure_test_role():
	if not frappe.db.exists("Role", _ROLE):
		frappe.get_doc(
			{"doctype": "Role", "role_name": _ROLE, "desk_access": 1}
		).insert(ignore_permissions=True)


def _ensure_assign_user():
	_ensure_test_role()
	if frappe.db.exists("User", _USER):
		return
	doc = frappe.get_doc(
		{
			"doctype": "User",
			"email": _USER,
			"first_name": "Assign",
			"send_welcome_email": 0,
			"enabled": 1,
		}
	)
	doc.append("roles", {"role": _ROLE})
	doc.insert(ignore_permissions=True)


class TestAssignmentValidForDate(FrappeTestCase):
	def test_open_ended(self):
		self.assertTrue(assignment_valid_for_date(valid_from=None, valid_to=None))
		d = getdate("2026-06-15")
		self.assertTrue(assignment_valid_for_date(valid_from=None, valid_to=None, as_of=d))

	def test_bounded(self):
		self.assertTrue(
			assignment_valid_for_date(
				valid_from="2026-01-01",
				valid_to="2026-12-31",
				as_of="2026-06-01",
			),
		)
		self.assertFalse(
			assignment_valid_for_date(
				valid_from="2026-01-01",
				valid_to="2026-01-31",
				as_of="2026-06-01",
			),
		)


class TestKenTenderAssignmentDocType(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		self.entity = _make_entity(_ENTITY)
		self.entity.insert()

	def tearDown(self):
		frappe.db.delete(ASSIGNMENT_DOCTYPE, {"target_docname": ("like", "_KT_ASG_%")})
		frappe.db.delete("Exception Record", {"business_id": ("like", "_KT_ASG_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": _ENTITY})
		frappe.db.commit()
		super().tearDown()

	def test_invalid_target_blocked(self):
		doc = frappe.get_doc(
			{
				"doctype": ASSIGNMENT_DOCTYPE,
				"assignment_type": "Other",
				"user": "Administrator",
				"target_doctype": "Exception Record",
				"target_docname": "NONEXISTENT-EXCEPTION",
				"active": 1,
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert)


class TestAssignmentAccessService(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		_ensure_assign_user()
		self.entity = _make_entity(_ENTITY)
		self.entity.insert()
		self.ex = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"business_id": _EX,
				"exception_type": "Other",
				"procuring_entity": self.entity.name,
				"triggered_by": "Administrator",
				"justification": "Assignment access test justification text.",
			}
		)
		self.ex.insert()

	def tearDown(self):
		frappe.db.delete(ASSIGNMENT_DOCTYPE, {"target_docname": _EX})
		frappe.db.delete("Exception Record", {"business_id": _EX})
		if frappe.db.exists("User", _USER):
			frappe.delete_doc("User", _USER, force=1, ignore_permissions=1)
		frappe.db.delete("Procuring Entity", {"entity_code": _ENTITY})
		frappe.db.commit()
		super().tearDown()

	def _insert_assignment(self, **kwargs):
		data = {
			"doctype": ASSIGNMENT_DOCTYPE,
			"assignment_type": "Committee",
			"user": "Administrator",
			"assignment_role": "Chair",
			"target_doctype": "Exception Record",
			"target_docname": self.ex.name,
			"active": 1,
		}
		data.update(kwargs)
		doc = frappe.get_doc(data)
		doc.insert(ignore_permissions=True)
		return doc

	def test_user_has_assignment_positive(self):
		self._insert_assignment()
		self.assertTrue(
			user_has_assignment(
				"Administrator",
				"Exception Record",
				self.ex.name,
			),
		)

	def test_user_has_assignment_inactive(self):
		self._insert_assignment(active=0)
		self.assertFalse(
			user_has_assignment(
				"Administrator",
				"Exception Record",
				self.ex.name,
				active_only=True,
			),
		)
		self.assertTrue(
			user_has_assignment(
				"Administrator",
				"Exception Record",
				self.ex.name,
				active_only=False,
			),
		)

	def test_user_has_assignment_wrong_user(self):
		self._insert_assignment()
		self.assertFalse(
			user_has_assignment(
				_USER,
				"Exception Record",
				self.ex.name,
			),
		)

	def test_user_has_assignment_type_filter(self):
		self._insert_assignment(assignment_type="Committee")
		self.assertTrue(
			user_has_assignment(
				"Administrator",
				"Exception Record",
				self.ex.name,
				assignment_type="Committee",
			),
		)
		self.assertFalse(
			user_has_assignment(
				"Administrator",
				"Exception Record",
				self.ex.name,
				assignment_type="Case Session",
			),
		)

	def test_user_has_assignment_role_filter(self):
		self._insert_assignment(assignment_role="Chair")
		self.assertTrue(
			user_has_assignment(
				"Administrator",
				"Exception Record",
				self.ex.name,
				assignment_role="Chair",
			),
		)
		self.assertFalse(
			user_has_assignment(
				"Administrator",
				"Exception Record",
				self.ex.name,
				assignment_role="Reviewer",
			),
		)

	def test_user_has_assignment_expired_validity(self):
		self._insert_assignment(
			valid_from="2020-01-01",
			valid_to="2020-01-31",
		)
		self.assertFalse(
			user_has_assignment(
				"Administrator",
				"Exception Record",
				self.ex.name,
			),
		)
		self.assertTrue(
			user_has_assignment(
				"Administrator",
				"Exception Record",
				self.ex.name,
				as_of_date="2020-01-15",
			),
		)

	def test_get_assignments_for_target(self):
		self._insert_assignment(assignment_role="Chair")
		self._insert_assignment(assignment_role="Member", user=_USER)
		rows = get_assignments_for_target("Exception Record", self.ex.name)
		self.assertEqual(len(rows), 2)

	def test_user_assignment_roles_on_target(self):
		self._insert_assignment(assignment_role="Chair")
		self._insert_assignment(assignment_role="Secretary")
		roles = user_assignment_roles_on_target(
			"Administrator",
			"Exception Record",
			self.ex.name,
		)
		self.assertEqual(roles, ["Chair", "Secretary"])

	def test_assigned_user_gets_access(self):
		self._insert_assignment(user=_USER, assignment_role="Reviewer")
		self.assertTrue(
			user_has_assignment(
				_USER,
				"Exception Record",
				self.ex.name,
			),
		)
