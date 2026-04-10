# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Role constants and lookups (PERM-002).

Maps **business role** labels from Roles and Permissions Guidance §2 to the
**KT UAT …** desk role names used in seeds and DocType/Report JSON. Add new
Frappe Role names here when UAT personas expand.
"""

from __future__ import annotations

from enum import Enum
from typing import FrozenSet

import frappe

__all__ = [
	"BUSINESS_ROLE",
	"UAT_ROLE",
	"all_uat_role_names",
	"user_has_any_uat_role",
	"uat_roles_for_business_role",
]


class BUSINESS_ROLE(str, Enum):
	"""Stable keys for documentation and code; not Frappe Role names."""

	DEPARTMENT_USER_REQUISITIONER = "department_user_requisitioner"
	HEAD_OF_DEPARTMENT = "head_of_department"
	FINANCE_APPROVER = "finance_approver"
	PROCUREMENT_OFFICER = "procurement_officer"
	OPENING_CHAIR = "opening_chair"
	EVALUATOR = "evaluator"
	EVALUATION_CHAIR = "evaluation_chair"
	ACCOUNTING_OFFICER = "accounting_officer"
	CONTRACT_MANAGER = "contract_manager"
	INSPECTION_OFFICER = "inspection_officer"
	STOREKEEPER = "storekeeper"
	ASSET_OFFICER = "asset_officer"
	SUPPLIER_USER = "supplier_user"
	SYSTEM_ADMINISTRATOR = "system_administrator"
	AUDITOR_OVERSIGHT = "auditor_oversight"
	STRATEGY_MANAGER = "strategy_manager"
	BUDGET_OFFICER = "budget_officer"


class UAT_ROLE(str, Enum):
	"""Frappe Role names for KenTender UAT / minimal golden seeds."""

	REQUISITIONER = "KT UAT Requisitioner"
	HOD = "KT UAT HOD"
	FINANCE = "KT UAT Finance Approver"
	PROCUREMENT = "KT UAT Procurement Officer"
	STRATEGY_MANAGER = "KT UAT Strategy Manager"
	BUDGET_OFFICER = "KT UAT Budget Officer"
	EVALUATOR = "KT UAT Evaluator"
	ACCOUNTING_OFFICER = "KT UAT Accounting Officer"
	SUPPLIER = "KT UAT Supplier"
	OPENING_CHAIR = "KT UAT Opening Chair"
	EVALUATION_CHAIR = "KT UAT Evaluation Chair"
	CONTRACT_MANAGER = "KT UAT Contract Manager"
	INSPECTION_OFFICER = "KT UAT Inspection Officer"
	STOREKEEPER = "KT UAT Storekeeper"
	ASSET_OFFICER = "KT UAT Asset Officer"
	AUDITOR = "KT UAT Auditor"


# Business-role key → one or more UAT Frappe roles (first is primary for seeds).
_BUSINESS_TO_UAT: dict[BUSINESS_ROLE, tuple[str, ...]] = {
	BUSINESS_ROLE.DEPARTMENT_USER_REQUISITIONER: (UAT_ROLE.REQUISITIONER.value,),
	BUSINESS_ROLE.HEAD_OF_DEPARTMENT: (UAT_ROLE.HOD.value,),
	BUSINESS_ROLE.FINANCE_APPROVER: (UAT_ROLE.FINANCE.value,),
	BUSINESS_ROLE.PROCUREMENT_OFFICER: (UAT_ROLE.PROCUREMENT.value,),
	BUSINESS_ROLE.OPENING_CHAIR: (UAT_ROLE.OPENING_CHAIR.value,),
	BUSINESS_ROLE.EVALUATOR: (UAT_ROLE.EVALUATOR.value,),
	BUSINESS_ROLE.EVALUATION_CHAIR: (UAT_ROLE.EVALUATION_CHAIR.value,),
	BUSINESS_ROLE.ACCOUNTING_OFFICER: (UAT_ROLE.ACCOUNTING_OFFICER.value,),
	BUSINESS_ROLE.CONTRACT_MANAGER: (UAT_ROLE.CONTRACT_MANAGER.value,),
	BUSINESS_ROLE.INSPECTION_OFFICER: (UAT_ROLE.INSPECTION_OFFICER.value,),
	BUSINESS_ROLE.STOREKEEPER: (UAT_ROLE.STOREKEEPER.value,),
	BUSINESS_ROLE.ASSET_OFFICER: (UAT_ROLE.ASSET_OFFICER.value,),
	BUSINESS_ROLE.SUPPLIER_USER: (UAT_ROLE.SUPPLIER.value,),
	BUSINESS_ROLE.SYSTEM_ADMINISTRATOR: ("System Manager",),
	BUSINESS_ROLE.AUDITOR_OVERSIGHT: (UAT_ROLE.AUDITOR.value,),
	BUSINESS_ROLE.STRATEGY_MANAGER: (UAT_ROLE.STRATEGY_MANAGER.value,),
	BUSINESS_ROLE.BUDGET_OFFICER: (UAT_ROLE.BUDGET_OFFICER.value,),
}


def uat_roles_for_business_role(key: BUSINESS_ROLE) -> tuple[str, ...]:
	return _BUSINESS_TO_UAT.get(key, ())


def all_uat_role_names() -> FrozenSet[str]:
	"""Every KT UAT … role string used in mappings (excludes System Manager)."""
	out: set[str] = set()
	for names in _BUSINESS_TO_UAT.values():
		for n in names:
			if n.startswith("KT UAT "):
				out.add(n)
	return frozenset(out)


def user_has_any_uat_role(user: str | None, *roles: UAT_ROLE) -> bool:
	"""True if *user* has at least one of the given UAT roles."""
	u = (user or frappe.session.user or "").strip()
	if not u:
		return False
	have = frozenset(frappe.get_roles(u))
	return any(r.value in have for r in roles)
