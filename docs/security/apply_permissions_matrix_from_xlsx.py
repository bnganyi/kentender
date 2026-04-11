#!/usr/bin/env python3
"""Regenerate DocType `permissions` from KenTender_Permissions_Matrix.xlsx (Permissions Matrix sheet).

Run from repo root (with bench venv Python that has openpyxl):
  /path/to/frappe-bench/env/bin/python apps/kentender_platform/docs/security/apply_permissions_matrix_from_xlsx.py

Then: bench --site <site> migrate
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]  # kentender_platform
XLSX = Path(__file__).resolve().parent / "KenTender_Permissions_Matrix.xlsx"

# xlsx Document/Entity -> folder slug under doctype/
DOC_TO_FOLDER: dict[str, str] = {
	"National Framework": "national_framework",
	"National Pillar": "national_pillar",
	"National Objective": "national_objective",
	"Entity Strategic Plan": "entity_strategic_plan",
	"Program": "strategic_program",
	"Sub-Program": "strategic_sub_program",
	"Indicator": "output_indicator",
	"Target": "performance_target",
	"Requisition": "purchase_requisition",
	"Procurement Plan": "procurement_plan",
	"Procurement Plan Item": "procurement_plan_item",
	"Procurement Template / Version": None,  # no shipped DocType with this exact name
	"Tender": "tender",
	"Bid / Submission": "bid_submission",
	"Opening Session": "bid_opening_session",
	"Evaluation Session": "evaluation_session",
	"Evaluation Score": "evaluation_record",
	"Evaluation Report": "evaluation_report",
	"Award Decision": "award_decision",  # xlsx Award Recommendation + Award Decision rows merged
	"Contract": "procurement_contract",
	"Inspection Record": "inspection_record",
	"Acceptance Record": "acceptance_record",
	"GRN (Goods Receipt Note)": "goods_receipt_note",
	"Asset": "kentender_asset",
	"Complaint": "complaint",
	"Approval Action": "kentender_approval_action",
	"Budget Ledger Entry": "budget_ledger_entry",
}

ROLE_MAP = {
	"HoD": "Head of Department",
	"Opening Chair": "Opening Committee Chair",
	"Opening Member": "Opening Committee Member",
	"Opening Secretary": "Opening Committee Secretary",
	"Evaluation Chair": "Evaluation Committee Chair",
	"Evaluation Secretary": "Evaluation Committee Secretary",
	"System": "System Manager",
	"Supplier (External)": "Supplier",
}


def norm_role(r: str) -> str:
	r = (r or "").strip()
	return ROLE_MAP.get(r, r)


def find_doctype_json(folder: str) -> Path | None:
	for base in (
		ROOT / "kentender_strategy" / "kentender_strategy" / "kentender_strategy" / "doctype",
		ROOT / "kentender_procurement" / "kentender_procurement" / "kentender_procurement" / "doctype",
		ROOT / "kentender_stores" / "kentender_stores" / "kentender_stores" / "doctype",
		ROOT / "kentender_assets" / "kentender_assets" / "kentender_assets" / "doctype",
		ROOT / "kentender_governance" / "kentender_governance" / "kentender_governance" / "doctype",
		ROOT / "kentender_budget" / "kentender_budget" / "kentender_budget" / "doctype",
		ROOT / "kentender" / "kentender" / "kentender" / "doctype",
	):
		p = base / folder / f"{folder}.json"
		if p.is_file():
			return p
	return None


def parse_tokens(codes: str) -> list[str]:
	"""Split permission codes like 'R C W S' or 'R AS CL'."""
	s = (codes or "").strip().upper()
	# normalize multi-letter
	s = re.sub(r"\s+", " ", s)
	parts = s.split()
	out: list[str] = []
	i = 0
	while i < len(parts):
		p = parts[i]
		if p in ("AS", "CL", "RP"):
			out.append(p)
		elif p == "R" and i + 1 < len(parts) and parts[i + 1] == "P":
			out.append("RP")
			i += 1
		else:
			out.append(p)
		i += 1
	return out


def tokens_to_perm(role: str, codes: str) -> dict:
	toks = parse_tokens(codes)
	p: dict = {
		"role": role,
		"email": 1,
		"export": 1,
		"print": 1,
		"share": 0,
		"read": 0,
		"write": 0,
		"create": 0,
		"delete": 0,
		"submit": 0,
		"cancel": 0,
		"report": 0,
	}
	for t in toks:
		if t == "R":
			p["read"] = 1
		elif t == "W":
			p["write"] = 1
			p["read"] = 1
		elif t == "C":
			p["create"] = 1
			p["read"] = 1
		elif t == "S":
			p["submit"] = 1
			p["read"] = 1
		elif t == "A":
			p["write"] = 1
			p["read"] = 1
		elif t == "X":
			p["cancel"] = 1
			p["read"] = 1
		elif t == "RP":
			p["report"] = 1
			p["read"] = 1
		elif t == "AS":
			p["read"] = 1
		elif t == "CL":
			p["read"] = 1
	return p


def system_manager_row() -> dict:
	return {
		"create": 1,
		"delete": 1,
		"email": 1,
		"export": 1,
		"print": 1,
		"read": 1,
		"report": 1,
		"role": "System Manager",
		"share": 1,
		"write": 1,
	}


def load_matrix_rows() -> list[tuple[str, str, str]]:
	wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
	ws = wb["Permissions Matrix"]
	rows: list[tuple[str, str, str]] = []
	for row in ws.iter_rows(min_row=2, values_only=True):
		if not row or not row[0]:
			continue
		doc, role, perm = row[0], row[1], row[2]
		if str(doc).strip() == "Document / Entity":
			continue
		rows.append((str(doc).strip(), str(role).strip(), str(perm or "").strip()))
	wb.close()
	return rows


def build_entity_permissions() -> dict[str, list[tuple[str, str]]]:
	"""entity label -> [(frappe_role, code), ...] merged for Award Decision from two xlsx sections."""
	from collections import defaultdict

	groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
	for doc, role, perm in load_matrix_rows():
		fr = norm_role(role)
		# Bid row: "Opening Committee" — map to Opening Committee Member for DocPerm baseline
		if doc == "Bid / Submission" and role.strip() == "Opening Committee":
			fr = "Opening Committee Member"
		groups[doc].append((fr, perm))
	return dict(groups)


def main() -> None:
	entity_perms = build_entity_permissions()
	skip = {"Procurement Template / Version"}

	for doc_label, folder in DOC_TO_FOLDER.items():
		if doc_label in skip or folder is None:
			print(f"SKIP (no DocType): {doc_label}")
			continue
		path = find_doctype_json(folder)
		if not path:
			print(f"MISSING FILE: {doc_label} -> {folder}")
			continue

		rows_in = []
		if doc_label == "Award Decision":
			rows_in = entity_perms.get("Award Recommendation", []) + entity_perms.get("Award Decision", [])
		else:
			rows_in = entity_perms.get(doc_label, [])

		if not rows_in:
			print(f"NO ROWS: {doc_label}")
			continue

		perms: list[dict] = [system_manager_row()]
		seen: set[str] = set()
		for fr, code in rows_in:
			if fr in seen:
				continue
			seen.add(fr)
			# Full admin row already covers System Manager; skip xlsx "System" -> System Manager duplicate.
			if fr == "System Manager":
				continue
			perms.append(tokens_to_perm(fr, code))

		data = json.loads(path.read_text(encoding="utf-8"))
		if data.get("doctype") != "DocType":
			print(f"NOT DOCTYPE: {path}")
			continue
		data["permissions"] = perms
		path.write_text(json.dumps(data, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8")
		print(f"OK {data.get('name')} <- {path.relative_to(ROOT)}")


if __name__ == "__main__":
	main()
