# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from frappe.tests.utils import FrappeTestCase

from kentender.uat.kt_test_local_users import is_kt_test_local_email


class TestKtTestLocalEmailConvention(FrappeTestCase):
	def test_is_kt_test_local_email(self):
		self.assertTrue(is_kt_test_local_email("_kt_pr04_approver@test.local"))
		self.assertTrue(is_kt_test_local_email("_KT_PR04@test.local"))
		self.assertFalse(is_kt_test_local_email("requisitioner.test@ken-tender.test"))
		self.assertFalse(is_kt_test_local_email("other@test.local"))
		self.assertFalse(is_kt_test_local_email(""))
