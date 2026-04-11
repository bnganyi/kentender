# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from frappe.tests.utils import FrappeTestCase

from kentender.uat.legacy_kt_roles import is_legacy_kt_uat_role_name


class TestLegacyKtRoleNaming(FrappeTestCase):
	def test_is_legacy_kt_uat_role_name(self):
		self.assertTrue(is_legacy_kt_uat_role_name("KT UAT Requisitioner"))
		self.assertFalse(is_legacy_kt_uat_role_name("KT UAT"))
		self.assertFalse(is_legacy_kt_uat_role_name("Requisitioner"))
		self.assertFalse(is_legacy_kt_uat_role_name("Strategy Administrator"))
