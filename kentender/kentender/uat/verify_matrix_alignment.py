# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Verify **Role Catalogue** (``KenTender_Permissions_Matrix.xlsx``) ↔ :class:`MATRIX_ROLE` ↔ minimal golden seed.

Run::

    bench --site <site> execute kentender.uat.verify_matrix_alignment.verify_matrix_alignment_console

Requires **openpyxl** (bench Python environment). Exits **1** if the workbook and registry diverge.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Sheet / column per workbook layout (Role Catalogue: Role Name = column C).
_EXCEL_ROLE_NAME_COL = 2  # 0-based index in row tuple

# Workbook labels that differ from Frappe ``Role.name`` / ``MATRIX_ROLE`` strings.
_EXCEL_TO_FRAPPE_ROLE: dict[str, str] = {
	"Head of Department (HoD)": "Head of Department",
	"Supplier (External)": "Supplier",
	# Matrix "System Administrator" → Frappe built-in full admin
	"System Administrator": "System Manager",
}


def _repo_root() -> Path:
	"""``apps/kentender_platform`` (parent of the ``kentender`` app folder)."""
	return Path(__file__).resolve().parents[3]


def _xlsx_path() -> Path:
	return _repo_root() / "docs" / "security" / "KenTender_Permissions_Matrix.xlsx"


def _load_excel_role_names() -> tuple[str, ...]:
	try:
		import openpyxl
	except ImportError as e:
		raise RuntimeError(
			"openpyxl is required to read KenTender_Permissions_Matrix.xlsx"
		) from e
	path = _xlsx_path()
	if not path.is_file():
		raise FileNotFoundError(f"Permissions matrix not found: {path}")
	wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
	ws = wb["Role Catalogue"]
	raw: list[str] = []
	for row in ws.iter_rows(min_row=2, values_only=True):
		if row and len(row) > _EXCEL_ROLE_NAME_COL and row[_EXCEL_ROLE_NAME_COL]:
			raw.append(str(row[_EXCEL_ROLE_NAME_COL]).strip())
	wb.close()
	names = sorted({_excel_normalize(r) for r in raw})
	return tuple(names)


def _excel_normalize(label: str) -> str:
	return _EXCEL_TO_FRAPPE_ROLE.get(label.strip(), label.strip())


def _matrix_unique_frappe_names() -> frozenset[str]:
	from kentender.permissions.registry import MATRIX_ROLE

	return frozenset(m.value for m in MATRIX_ROLE)


def _golden_seed_roles() -> frozenset[str]:
	from kentender.uat.minimal_golden.dataset import load_minimal_golden_dataset

	ds = load_minimal_golden_dataset()
	out: set[str] = set()
	for sec in ("internal", "suppliers"):
		for row in (ds.get("users") or {}).get(sec) or []:
			r = (row.get("role") or "").strip()
			if r:
				out.add(r)
	return frozenset(out)


def verify_excel_vs_registry() -> dict[str, Any]:
	"""Compare Role Catalogue to :class:`MATRIX_ROLE` unique values (after label normalization)."""
	excel = frozenset(_load_excel_role_names())
	matrix = _matrix_unique_frappe_names()
	only_excel = sorted(excel - matrix)
	only_matrix = sorted(matrix - excel)
	return {
		"ok": len(only_excel) == 0 and len(only_matrix) == 0,
		"excel_role_count": len(excel),
		"matrix_unique_count": len(matrix),
		"only_in_excel_not_in_registry": only_excel,
		"only_in_registry_not_in_excel": only_matrix,
		"xlsx_path": str(_xlsx_path()),
	}


def verify_golden_user_role_coverage() -> dict[str, Any]:
	"""Matrix roles that have no **dedicated** minimal-golden test user (single role per user).

	``minimal_golden_canonical.json`` is expected to include one desk (or portal) user per
	Role Catalogue row: internal **System User** accounts for every ``MATRIX_ROLE`` value
	except **Supplier** (two **Website User** supplier bidders share that role).
	"""
	matrix = _matrix_unique_frappe_names()
	seed = _golden_seed_roles()
	missing = sorted(matrix - seed)
	return {
		"golden_distinct_roles": len(seed),
		"matrix_roles_without_golden_user": missing,
		"count_matrix_roles_without_golden_user": len(missing),
	}


def verify_matrix_alignment() -> dict[str, Any]:
	"""Full structured report for tooling / CI."""
	reg = verify_excel_vs_registry()
	cov = verify_golden_user_role_coverage()
	golden_ok = cov["count_matrix_roles_without_golden_user"] == 0
	return {
		"registry_vs_xlsx": reg,
		"golden_seed_coverage": cov,
		"overall_ok": reg["ok"] and golden_ok,
	}


def verify_matrix_alignment_console() -> None:
	"""Print report; exit **1** if xlsx/registry diverge or golden seed is missing a matrix role."""
	try:
		r = verify_matrix_alignment()
	except Exception:
		raise
	reg = r["registry_vs_xlsx"]
	cov = r["golden_seed_coverage"]

	print("KenTender matrix alignment verification")
	print("======================================")
	print(f"Workbook: {reg['xlsx_path']}")
	print(
		f"Role Catalogue (normalized): {reg['excel_role_count']} | "
		f"MATRIX_ROLE unique values: {reg['matrix_unique_count']}"
	)
	if reg["only_in_excel_not_in_registry"]:
		print("\nFAIL: In xlsx Role Catalogue but not in MATRIX_ROLE:")
		for x in reg["only_in_excel_not_in_registry"]:
			print(f"  - {x}")
	if reg["only_in_registry_not_in_excel"]:
		print("\nFAIL: In MATRIX_ROLE but not in xlsx Role Catalogue (normalized):")
		for x in reg["only_in_registry_not_in_excel"]:
			print(f"  - {x}")
	if reg["ok"]:
		print("\nOK: Excel Role Catalogue matches MATRIX_ROLE (after HoD / Supplier / System Admin mapping).")
	else:
		print("\nRegistry vs xlsx: FAILED")

	print(
		f"\nMinimal golden seed: {cov['golden_distinct_roles']} distinct Frappe Role(s) "
		f"across test users (internal + suppliers)."
	)
	n_missing = cov["count_matrix_roles_without_golden_user"]
	if n_missing:
		print(
			f"\nFAIL: {n_missing} matrix role(s) have no golden test user "
			"(see ``users`` in minimal_golden_canonical.json)."
		)
		for role in cov["matrix_roles_without_golden_user"]:
			print(f"  - {role}")
		raise SystemExit(1)
	print(
		f"\nOK: Every Role Catalogue / ``MATRIX_ROLE`` value is represented in the golden seed "
		f"({cov['golden_distinct_roles']} distinct roles; **Supplier** ×2 portal users + one user per other role)."
	)

	if not r["overall_ok"]:
		raise SystemExit(1)
	print("\nDone.")


if __name__ == "__main__":
	# Allow: python -m kentender.uat.verify_matrix_alignment
	verify_matrix_alignment_console()
