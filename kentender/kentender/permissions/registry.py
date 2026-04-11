# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Role constants and lookups (PERM-002).

Maps **business role** keys to Frappe **Role.name** strings from
`docs/security/KenTender Roles and Permissions Matrix.md` (plain matrix labels).

**System admin:** The matrix lists *System Administrator*; Frappe uses **System Manager**
for full technical admin — use `MATRIX_ROLE.SYSTEM_MANAGER` in code and DocPerms.
"""

from __future__ import annotations

from enum import Enum
from typing import FrozenSet

import frappe

__all__ = [
	"BUSINESS_ROLE",
	"MATRIX_ROLE",
	"all_matrix_role_names",
	"matrix_roles_for_business_role",
	"uat_roles_for_business_role",
	"user_has_any_matrix_role",
	# Back-compat (deprecated): prefer MATRIX_ROLE / matrix_* helpers
	"UAT_ROLE",
	"all_uat_role_names",
	"user_has_any_uat_role",
]


class BUSINESS_ROLE(str, Enum):
	"""Stable keys for documentation and code; not Frappe Role names."""

	# §2.0 Strategy & alignment
	STRATEGY_ADMINISTRATOR = "strategy_administrator"
	STRATEGY_REVIEWER = "strategy_reviewer"
	# §2.1 Requisition & planning
	DEPARTMENT_USER_REQUISITIONER = "department_user_requisitioner"
	DEPARTMENT_REVIEWER = "department_reviewer"
	HEAD_OF_DEPARTMENT = "head_of_department"
	PROCUREMENT_PLANNER = "procurement_planner"
	PLANNING_AUTHORITY = "planning_authority"
	# §2.2 Finance
	FINANCE_OFFICER = "finance_officer"
	BUDGET_CONTROLLER = "budget_controller"
	ACCOUNTING_OFFICER = "accounting_officer"
	# §2.3 Procurement
	PROCUREMENT_OFFICER = "procurement_officer"
	TENDER_COMMITTEE_SECRETARY = "tender_committee_secretary"
	TENDER_COMMITTEE_CHAIR = "tender_committee_chair"
	TENDER_COMMITTEE_MEMBER = "tender_committee_member"
	# §2.4 Supplier
	SUPPLIER_USER = "supplier_user"
	SUPPLIER_COMPLIANCE_REVIEWER = "supplier_compliance_reviewer"
	# §2.5 Contract
	CONTRACT_MANAGER = "contract_manager"
	AUTHORIZED_SIGNATORY = "authorized_signatory"
	# §2.6 Inspection
	INSPECTOR = "inspector"
	# §2.7 Stores & assets
	STOREKEEPER = "storekeeper"
	STORES_SUPERVISOR = "stores_supervisor"
	ASSET_OFFICER = "asset_officer"
	ASSET_CUSTODIAN = "asset_custodian"
	# §2.8 Oversight
	AUDITOR_OVERSIGHT = "auditor_oversight"
	COMPLAINT_REVIEWER = "complaint_reviewer"
	# §3 Session (Frappe Role + assignment)
	OPENING_COMMITTEE_CHAIR = "opening_committee_chair"
	OPENING_COMMITTEE_MEMBER = "opening_committee_member"
	OPENING_COMMITTEE_SECRETARY = "opening_committee_secretary"
	EVALUATOR = "evaluator"
	EVALUATION_COMMITTEE_CHAIR = "evaluation_committee_chair"
	EVALUATION_COMMITTEE_SECRETARY = "evaluation_committee_secretary"
	TECHNICAL_EXPERT = "technical_expert"
	ACCEPTANCE_COMMITTEE_CHAIR = "acceptance_committee_chair"
	ACCEPTANCE_COMMITTEE_MEMBER = "acceptance_committee_member"
	# §4 Administrative (custom roles + System Manager)
	SYSTEM_ADMINISTRATOR = "system_administrator"
	TEMPLATE_ADMINISTRATOR = "template_administrator"
	WORKFLOW_ADMINISTRATOR = "workflow_administrator"
	PERMISSION_ADMINISTRATOR = "permission_administrator"
	MASTER_DATA_ADMINISTRATOR = "master_data_administrator"


class MATRIX_ROLE(str, Enum):
	"""Frappe Role.name values aligned to the KenTender matrix (plain labels)."""

	# §2.0 Strategy & alignment
	STRATEGY_ADMINISTRATOR = "Strategy Administrator"
	STRATEGY_REVIEWER = "Strategy Reviewer"
	# §2 Permanent
	REQUISITIONER = "Requisitioner"
	DEPARTMENT_REVIEWER = "Department Reviewer"
	HEAD_OF_DEPARTMENT = "Head of Department"
	PROCUREMENT_PLANNER = "Procurement Planner"
	PLANNING_AUTHORITY = "Planning Authority"
	FINANCE_OFFICER = "Finance Officer"
	BUDGET_CONTROLLER = "Budget Controller"
	ACCOUNTING_OFFICER = "Accounting Officer"
	PROCUREMENT_OFFICER = "Procurement Officer"
	TENDER_COMMITTEE_SECRETARY = "Tender Committee Secretary"
	TENDER_COMMITTEE_CHAIR = "Tender Committee Chair"
	TENDER_COMMITTEE_MEMBER = "Tender Committee Member"
	SUPPLIER = "Supplier"
	SUPPLIER_COMPLIANCE_REVIEWER = "Supplier Compliance Reviewer"
	CONTRACT_MANAGER = "Contract Manager"
	AUTHORIZED_SIGNATORY = "Authorized Signatory"
	INSPECTOR = "Inspector"
	STOREKEEPER = "Storekeeper"
	STORES_SUPERVISOR = "Stores Supervisor"
	ASSET_OFFICER = "Asset Officer"
	ASSET_CUSTODIAN = "Asset Custodian"
	AUDITOR = "Auditor"
	COMPLAINT_REVIEWER = "Complaint Reviewer"
	# §3 Session / hybrid
	OPENING_COMMITTEE_CHAIR = "Opening Committee Chair"
	OPENING_COMMITTEE_MEMBER = "Opening Committee Member"
	OPENING_COMMITTEE_SECRETARY = "Opening Committee Secretary"
	EVALUATOR = "Evaluator"
	EVALUATION_COMMITTEE_CHAIR = "Evaluation Committee Chair"
	EVALUATION_COMMITTEE_SECRETARY = "Evaluation Committee Secretary"
	TECHNICAL_EXPERT = "Technical Expert"
	ACCEPTANCE_COMMITTEE_CHAIR = "Acceptance Committee Chair"
	ACCEPTANCE_COMMITTEE_MEMBER = "Acceptance Committee Member"
	# Frappe built-in full admin (matrix "System Administrator")
	SYSTEM_MANAGER = "System Manager"
	# §4 Administrative (custom Role documents)
	TEMPLATE_ADMINISTRATOR = "Template Administrator"
	WORKFLOW_ADMINISTRATOR = "Workflow Administrator"
	PERMISSION_ADMINISTRATOR = "Permission Administrator"
	MASTER_DATA_ADMINISTRATOR = "Master Data Administrator"
	# Legacy aliases (same value as canonical members — prefer canonical names in new code)
	HOD = "Head of Department"
	FINANCE = "Finance Officer"
	PROCUREMENT = "Procurement Officer"
	OPENING_CHAIR = "Opening Committee Chair"
	EVALUATION_CHAIR = "Evaluation Committee Chair"
	INSPECTION_OFFICER = "Inspector"


_BUSINESS_TO_MATRIX: dict[BUSINESS_ROLE, tuple[str, ...]] = {
	BUSINESS_ROLE.STRATEGY_ADMINISTRATOR: (MATRIX_ROLE.STRATEGY_ADMINISTRATOR.value,),
	BUSINESS_ROLE.STRATEGY_REVIEWER: (MATRIX_ROLE.STRATEGY_REVIEWER.value,),
	BUSINESS_ROLE.DEPARTMENT_USER_REQUISITIONER: (MATRIX_ROLE.REQUISITIONER.value,),
	BUSINESS_ROLE.DEPARTMENT_REVIEWER: (MATRIX_ROLE.DEPARTMENT_REVIEWER.value,),
	BUSINESS_ROLE.HEAD_OF_DEPARTMENT: (MATRIX_ROLE.HEAD_OF_DEPARTMENT.value,),
	BUSINESS_ROLE.PROCUREMENT_PLANNER: (MATRIX_ROLE.PROCUREMENT_PLANNER.value,),
	BUSINESS_ROLE.PLANNING_AUTHORITY: (MATRIX_ROLE.PLANNING_AUTHORITY.value,),
	BUSINESS_ROLE.FINANCE_OFFICER: (MATRIX_ROLE.FINANCE_OFFICER.value,),
	BUSINESS_ROLE.BUDGET_CONTROLLER: (MATRIX_ROLE.BUDGET_CONTROLLER.value,),
	BUSINESS_ROLE.ACCOUNTING_OFFICER: (MATRIX_ROLE.ACCOUNTING_OFFICER.value,),
	BUSINESS_ROLE.PROCUREMENT_OFFICER: (MATRIX_ROLE.PROCUREMENT_OFFICER.value,),
	BUSINESS_ROLE.TENDER_COMMITTEE_SECRETARY: (MATRIX_ROLE.TENDER_COMMITTEE_SECRETARY.value,),
	BUSINESS_ROLE.TENDER_COMMITTEE_CHAIR: (MATRIX_ROLE.TENDER_COMMITTEE_CHAIR.value,),
	BUSINESS_ROLE.TENDER_COMMITTEE_MEMBER: (MATRIX_ROLE.TENDER_COMMITTEE_MEMBER.value,),
	BUSINESS_ROLE.SUPPLIER_USER: (MATRIX_ROLE.SUPPLIER.value,),
	BUSINESS_ROLE.SUPPLIER_COMPLIANCE_REVIEWER: (MATRIX_ROLE.SUPPLIER_COMPLIANCE_REVIEWER.value,),
	BUSINESS_ROLE.CONTRACT_MANAGER: (MATRIX_ROLE.CONTRACT_MANAGER.value,),
	BUSINESS_ROLE.AUTHORIZED_SIGNATORY: (MATRIX_ROLE.AUTHORIZED_SIGNATORY.value,),
	BUSINESS_ROLE.INSPECTOR: (MATRIX_ROLE.INSPECTOR.value,),
	BUSINESS_ROLE.STOREKEEPER: (MATRIX_ROLE.STOREKEEPER.value,),
	BUSINESS_ROLE.STORES_SUPERVISOR: (MATRIX_ROLE.STORES_SUPERVISOR.value,),
	BUSINESS_ROLE.ASSET_OFFICER: (MATRIX_ROLE.ASSET_OFFICER.value,),
	BUSINESS_ROLE.ASSET_CUSTODIAN: (MATRIX_ROLE.ASSET_CUSTODIAN.value,),
	BUSINESS_ROLE.AUDITOR_OVERSIGHT: (MATRIX_ROLE.AUDITOR.value,),
	BUSINESS_ROLE.COMPLAINT_REVIEWER: (MATRIX_ROLE.COMPLAINT_REVIEWER.value,),
	BUSINESS_ROLE.OPENING_COMMITTEE_CHAIR: (MATRIX_ROLE.OPENING_COMMITTEE_CHAIR.value,),
	BUSINESS_ROLE.OPENING_COMMITTEE_MEMBER: (MATRIX_ROLE.OPENING_COMMITTEE_MEMBER.value,),
	BUSINESS_ROLE.OPENING_COMMITTEE_SECRETARY: (MATRIX_ROLE.OPENING_COMMITTEE_SECRETARY.value,),
	BUSINESS_ROLE.EVALUATOR: (MATRIX_ROLE.EVALUATOR.value,),
	BUSINESS_ROLE.EVALUATION_COMMITTEE_CHAIR: (MATRIX_ROLE.EVALUATION_COMMITTEE_CHAIR.value,),
	BUSINESS_ROLE.EVALUATION_COMMITTEE_SECRETARY: (MATRIX_ROLE.EVALUATION_COMMITTEE_SECRETARY.value,),
	BUSINESS_ROLE.TECHNICAL_EXPERT: (MATRIX_ROLE.TECHNICAL_EXPERT.value,),
	BUSINESS_ROLE.ACCEPTANCE_COMMITTEE_CHAIR: (MATRIX_ROLE.ACCEPTANCE_COMMITTEE_CHAIR.value,),
	BUSINESS_ROLE.ACCEPTANCE_COMMITTEE_MEMBER: (MATRIX_ROLE.ACCEPTANCE_COMMITTEE_MEMBER.value,),
	BUSINESS_ROLE.SYSTEM_ADMINISTRATOR: (MATRIX_ROLE.SYSTEM_MANAGER.value,),
	BUSINESS_ROLE.TEMPLATE_ADMINISTRATOR: (MATRIX_ROLE.TEMPLATE_ADMINISTRATOR.value,),
	BUSINESS_ROLE.WORKFLOW_ADMINISTRATOR: (MATRIX_ROLE.WORKFLOW_ADMINISTRATOR.value,),
	BUSINESS_ROLE.PERMISSION_ADMINISTRATOR: (MATRIX_ROLE.PERMISSION_ADMINISTRATOR.value,),
	BUSINESS_ROLE.MASTER_DATA_ADMINISTRATOR: (MATRIX_ROLE.MASTER_DATA_ADMINISTRATOR.value,),
}


def matrix_roles_for_business_role(key: BUSINESS_ROLE) -> tuple[str, ...]:
	return _BUSINESS_TO_MATRIX.get(key, ())


def uat_roles_for_business_role(key: BUSINESS_ROLE) -> tuple[str, ...]:
	"""Deprecated: use ``matrix_roles_for_business_role``."""
	return matrix_roles_for_business_role(key)


# KenTender matrix catalogue roles (excludes Frappe built-in System Manager from the seed persona set)
_MATRIX_CATALOG_EXCLUDE = frozenset({MATRIX_ROLE.SYSTEM_MANAGER.value})


def all_matrix_role_names() -> FrozenSet[str]:
	"""Frappe Role names in :class:`MATRIX_ROLE` except ``System Manager``."""
	return frozenset(r.value for r in MATRIX_ROLE if r.value not in _MATRIX_CATALOG_EXCLUDE)


def all_uat_role_names() -> FrozenSet[str]:
	"""Deprecated: use ``all_matrix_role_names``."""
	return all_matrix_role_names()


def user_has_any_matrix_role(user: str | None, *roles: MATRIX_ROLE) -> bool:
	"""True if *user* has at least one of the given matrix roles."""
	u = (user or frappe.session.user or "").strip()
	if not u:
		return False
	have = frozenset(frappe.get_roles(u))
	return any(r.value in have for r in roles)


def user_has_any_uat_role(user: str | None, *roles: MATRIX_ROLE) -> bool:
	"""Deprecated: use ``user_has_any_matrix_role``."""
	return user_has_any_matrix_role(user, *roles)


# Back-compat: UAT_ROLE was the old name for seeded desk roles
UAT_ROLE = MATRIX_ROLE
