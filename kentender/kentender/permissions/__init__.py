# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""KenTender permission vocabulary and integration surface (PERM-001–004).

Domain rules stay in owning apps; this package holds shared role constants,
report helpers, and re-exports for scope utilities.
"""

from kentender.permissions.registry import (
	BUSINESS_ROLE,
	UAT_ROLE,
	all_uat_role_names,
	user_has_any_uat_role,
)
from kentender.permissions.reports import user_can_open_script_report

__all__ = [
	"BUSINESS_ROLE",
	"UAT_ROLE",
	"all_uat_role_names",
	"user_has_any_uat_role",
	"user_can_open_script_report",
]
