#!/usr/bin/env python3
"""Validate workspace config references against live Frappe site metadata.

Usage:
  python validate_workspace_assets.py --site <site-name>
  python validate_workspace_assets.py --site <site-name> --write-report
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import frappe


BASE = Path(__file__).resolve().parent
BENCH_ROOT = BASE.parents[4]


def _load_jsons(folder: str) -> list[dict]:
    docs = []
    for path in sorted((BASE / folder).glob("*.json")):
        with path.open(encoding="utf-8") as f:
            payload = json.load(f)
        payload["_source_file"] = str(path.relative_to(BASE))
        docs.append(payload)
    return docs


def _push(refs: dict[str, set[str]], key: str, value: str | None) -> None:
    if value and isinstance(value, str):
        refs[key].add(value)


def collect_references() -> dict[str, set[str]]:
    refs: dict[str, set[str]] = defaultdict(set)

    workspaces = _load_jsons("workspaces")
    sidebars = _load_jsons("sidebars")
    desktop_icons = _load_jsons("desktop_icons")

    for ws in workspaces:
        _push(refs, "Workspace", ws.get("name"))

        for row in ws.get("shortcuts") or []:
            _push(refs, row.get("type"), row.get("link_to"))

        for row in ws.get("links") or []:
            if row.get("type") == "Link":
                _push(refs, row.get("link_type"), row.get("link_to"))

        for row in ws.get("quick_lists") or []:
            _push(refs, "DocType", row.get("document_type"))
            _push(refs, "Quick List", row.get("label"))

        for row in ws.get("number_cards") or []:
            _push(refs, "Number Card", row.get("label"))

        for row in ws.get("charts") or []:
            _push(refs, "Dashboard Chart", row.get("label"))

    for sb in sidebars:
        _push(refs, "Workspace Sidebar", sb.get("name"))
        for row in sb.get("items") or []:
            if row.get("type") == "Link":
                _push(refs, row.get("link_type"), row.get("link_to"))

    for di in desktop_icons:
        _push(refs, "Desktop Icon", di.get("name"))
        _push(refs, di.get("link_type"), di.get("link_to"))
        for role in di.get("roles") or []:
            _push(refs, "Role", role.get("role"))

    return refs


def exists(doctype: str, name: str) -> bool:
    try:
        return bool(frappe.db.exists(doctype, name))
    except Exception:
        return False


def validate_against_site(refs: dict[str, set[str]]) -> dict:
    supported = {
        "DocType",
        "Page",
        "Report",
        "Workspace",
        "Workspace Sidebar",
        "Quick List",
        "Number Card",
        "Dashboard Chart",
        "Desktop Icon",
        "Role",
    }

    result = {"missing": defaultdict(list), "present_counts": {}, "ignored_types": {}}
    for ref_type, names in sorted(refs.items()):
        names = sorted(names)
        if ref_type not in supported:
            result["ignored_types"][ref_type] = names
            continue

        present = 0
        for name in names:
            if exists(ref_type, name):
                present += 1
            else:
                result["missing"][ref_type].append(name)
        result["present_counts"][ref_type] = {"present": present, "total": len(names)}
    return result


def format_report(site: str, refs: dict[str, set[str]], validation: dict) -> str:
    lines: list[str] = []
    lines.append(f"# KenTender Workspace Config Validation ({site})")
    lines.append("")
    lines.append(f"Source: `{BASE}`")
    lines.append("")

    lines.append("## Coverage")
    for ref_type in sorted(validation["present_counts"].keys()):
        counts = validation["present_counts"][ref_type]
        lines.append(f"- {ref_type}: {counts['present']}/{counts['total']} present")

    if validation["ignored_types"]:
        lines.append("")
        lines.append("## Ignored reference types")
        for ref_type, names in sorted(validation["ignored_types"].items()):
            lines.append(f"- {ref_type}: {len(names)} entries")

    lines.append("")
    lines.append("## Missing references")
    any_missing = False
    for ref_type in sorted(validation["missing"].keys()):
        missing = validation["missing"][ref_type]
        if not missing:
            continue
        any_missing = True
        lines.append(f"### {ref_type} ({len(missing)})")
        for name in missing:
            lines.append(f"- `{name}`")
        lines.append("")

    if not any_missing:
        lines.append("- None")

    lines.append("")
    lines.append("## Counts by config type")
    for ref_type in sorted(refs.keys()):
        lines.append(f"- {ref_type}: {len(refs[ref_type])}")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument(
        "--report-path",
        default=str(BASE / "validation-report.md"),
        help="Path for markdown report when --write-report is set.",
    )
    args = parser.parse_args()

    frappe.init(site=args.site, sites_path=str(BENCH_ROOT / "sites"))
    frappe.connect()
    try:
        refs = collect_references()
        validation = validate_against_site(refs)
        report = format_report(args.site, refs, validation)
    finally:
        frappe.destroy()

    print(report)
    if args.write_report:
        out = Path(args.report_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"Report written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
