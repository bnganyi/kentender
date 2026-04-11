# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import unittest

from kentender.permissions.registry import (
	BUSINESS_ROLE,
	MATRIX_ROLE,
	all_matrix_role_names,
	matrix_roles_for_business_role,
)


class TestPermissionsRegistry(unittest.TestCase):
	def test_matrix_roles_for_business_role_maps_hod(self):
		names = matrix_roles_for_business_role(BUSINESS_ROLE.HEAD_OF_DEPARTMENT)
		self.assertIn(MATRIX_ROLE.HEAD_OF_DEPARTMENT.value, names)

	def test_all_matrix_role_names_includes_core_personas(self):
		names = all_matrix_role_names()
		self.assertIn(MATRIX_ROLE.REQUISITIONER.value, names)
		self.assertIn(MATRIX_ROLE.AUDITOR.value, names)
		self.assertIn(MATRIX_ROLE.STRATEGY_ADMINISTRATOR.value, names)
		self.assertIn(MATRIX_ROLE.STRATEGY_REVIEWER.value, names)

	def test_strategy_business_roles_map(self):
		self.assertIn(
			MATRIX_ROLE.STRATEGY_ADMINISTRATOR.value,
			matrix_roles_for_business_role(BUSINESS_ROLE.STRATEGY_ADMINISTRATOR),
		)

	def test_auditor_business_role(self):
		self.assertIn(
			MATRIX_ROLE.AUDITOR.value,
			matrix_roles_for_business_role(BUSINESS_ROLE.AUDITOR_OVERSIGHT),
		)
