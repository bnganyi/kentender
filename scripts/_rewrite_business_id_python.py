#!/usr/bin/env python3
"""Mechanical rewrites: business_id -> name / remove audit kw (run from kentender_platform root)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {"__pycache__", ".git", "node_modules"}


def process_file(p: Path) -> bool:
	raw = p.read_text(encoding="utf-8")
	orig = raw
	# DocType controller patterns
	raw = raw.replace("code_title_label(self.business_id,", "code_title_label(self.name,")
	raw = raw.replace("(self.business_id or \"\").strip(),", "(self.name or \"\").strip(),")
	raw = raw.replace("(self.business_id or \"\").strip()", "(self.name or \"\").strip()")
	raw = raw.replace("self.business_id", "self.name")
	# Common frappe patterns
	raw = raw.replace('.get("business_id")', '.get("name")')
	raw = raw.replace("get('business_id')", "get('name')")
	raw = raw.replace('"business_id":', '"name":')
	raw = raw.replace("'business_id':", "'name':")
	raw = raw.replace("filters={\"business_id\":", "filters={\"name\":")
	raw = raw.replace("filters={'business_id':", "filters={'name':")
	raw = raw.replace("{\"business_id\":", "{\"name\":")
	raw = raw.replace("('business_id',", "('name',")
	raw = raw.replace('("business_id",', '("name",')
	raw = raw.replace("pluck=\"business_id\"", "pluck=\"name\"")
	raw = raw.replace("pluck='business_id'", "pluck='name'")
	raw = raw.replace("delete(\"business_id\",", "delete(\"name\",")
	# SQL / db.delete column name
	raw = raw.replace('{"business_id":', '{"name":')
	# Remove log_audit_event business_id kw (multiline friendly)
	raw = re.sub(r"\n\s*business_id=[^,\n)]+,", "", raw)
	raw = re.sub(r",\s*business_id=[^,\n)]+", "", raw)
	# Hash payload keys in audit - already removed by replacing "business_id": in dicts - careful
	# Restore audit hash_payload if we broke it - audit_event_service will be hand-edited
	if raw != orig:
		p.write_text(raw, encoding="utf-8")
		return True
	return False


def main() -> int:
	n = 0
	for p in ROOT.rglob("*.py"):
		if any(x in p.parts for x in SKIP_DIRS):
			continue
		if "scripts/_rewrite" in str(p):
			continue
		if process_file(p):
			print(p.relative_to(ROOT))
			n += 1
	print("modified", n, "files")
	return 0


if __name__ == "__main__":
	sys.exit(main())
