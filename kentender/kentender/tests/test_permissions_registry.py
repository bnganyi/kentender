# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import unittest

from kentender.permissions.registry import (
	BUSINESS_ROLE,
	UAT_ROLE,
	all_uat_role_names,
	uat_roles_for_business_role,
)


class TestPermissionsRegistry(unittest.TestCase):
	def test_uat_roles_for_business_role_maps_hod(self):
		names = uat_roles_for_business_role(BUSINESS_ROLE.HEAD_OF_DEPARTMENT)
		self.assertIn(UAT_ROLE.HOD.value, names)

	def test_all_uat_role_names_includes_core_personas(self):
		names = all_uat_role_names()
		self.assertIn(UAT_ROLE.REQUISITIONER.value, names)
		self.assertIn(UAT_ROLE.AUDITOR.value, names)

	def test_auditor_business_role(self):
		self.assertIn(UAT_ROLE.AUDITOR.value, uat_roles_for_business_role(BUSINESS_ROLE.AUDITOR_OVERSIGHT))
