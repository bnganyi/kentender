# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from frappe.tests.utils import FrappeTestCase

from kentender.uat.verify_matrix_alignment import (
	_repo_root,
	verify_excel_vs_registry,
	verify_golden_user_role_coverage,
)


class TestVerifyMatrixAlignment(FrappeTestCase):
	def test_excel_role_catalogue_matches_matrix_role_when_workbook_present(self):
		xlsx = _repo_root() / "docs" / "security" / "KenTender_Permissions_Matrix.xlsx"
		if not xlsx.is_file():
			return
		reg = verify_excel_vs_registry()
		self.assertTrue(
			reg["ok"],
			msg=(
				f"only_in_excel={reg['only_in_excel_not_in_registry']} "
				f"only_in_matrix={reg['only_in_registry_not_in_excel']}"
			),
		)

	def test_golden_seed_covers_every_matrix_role(self):
		cov = verify_golden_user_role_coverage()
		self.assertEqual(
			cov["count_matrix_roles_without_golden_user"],
			0,
			msg=f"Missing golden users for roles: {cov['matrix_roles_without_golden_user']}",
		)
