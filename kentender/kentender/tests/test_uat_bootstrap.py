# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.uat.bootstrap import KT_UAT_ROLES, ensure_uat_roles


class TestUatBootstrap(FrappeTestCase):
	def test_ensure_uat_roles_idempotent(self):
		self.assertGreaterEqual(len(KT_UAT_ROLES), 7)
		ensure_uat_roles()
		ensure_uat_roles()
		for role_name, _desc in KT_UAT_ROLES:
			self.assertTrue(frappe.db.exists("Role", role_name))
