# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""KenTender permission vocabulary and integration surface (PERM-001–004).

Domain rules stay in owning apps; this package holds shared role constants,
report helpers, and re-exports for scope utilities.
"""

from kentender.permissions.registry import (
	BUSINESS_ROLE,
	MATRIX_ROLE,
	UAT_ROLE,
	all_matrix_role_names,
	all_uat_role_names,
	matrix_roles_for_business_role,
	uat_roles_for_business_role,
	user_has_any_matrix_role,
	user_has_any_uat_role,
)
from kentender.permissions.reports import user_can_open_script_report

__all__ = [
	"BUSINESS_ROLE",
	"MATRIX_ROLE",
	"UAT_ROLE",
	"all_matrix_role_names",
	"all_uat_role_names",
	"matrix_roles_for_business_role",
	"uat_roles_for_business_role",
	"user_has_any_matrix_role",
	"user_has_any_uat_role",
	"user_can_open_script_report",
]
