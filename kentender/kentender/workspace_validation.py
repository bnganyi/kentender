from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import frappe


def _base() -> Path:
    # get_app_path("kentender") resolves to .../apps/kentender/kentender (python package root)
    # UX assets live one level up at .../apps/kentender/ux
    return Path(frappe.get_app_path("kentender")).parent / "ux" / "kentender-workspace-configs"


def _load_jsons(folder: str) -> list[dict]:
    base = _base()
    docs = []
    for path in sorted((base / folder).glob("*.json")):
        with path.open(encoding="utf-8") as f:
            payload = json.load(f)
        payload["_source_file"] = str(path.relative_to(base))
        docs.append(payload)
    return docs


def _push(refs: dict[str, set[str]], key: str | None, value: str | None) -> None:
    if key and value and isinstance(key, str) and isinstance(value, str):
        refs[key].add(value)


def _collect_references() -> dict[str, set[str]]:
    refs: dict[str, set[str]] = defaultdict(set)

    for ws in _load_jsons("workspaces"):
        _push(refs, "Workspace", ws.get("name"))
        for row in ws.get("shortcuts") or []:
            _push(refs, row.get("type"), row.get("link_to"))
        for row in ws.get("links") or []:
            if row.get("type") == "Link":
                _push(refs, row.get("link_type"), row.get("link_to"))
        for row in ws.get("quick_lists") or []:
            _push(refs, "DocType", row.get("document_type"))
        for row in ws.get("number_cards") or []:
            _push(refs, "Number Card", row.get("number_card_name") or row.get("label"))
        for row in ws.get("charts") or []:
            _push(refs, "Dashboard Chart", row.get("chart_name") or row.get("label"))

    for sb in _load_jsons("sidebars"):
        _push(refs, "Workspace Sidebar", sb.get("name"))
        for row in sb.get("items") or []:
            if row.get("type") == "Link":
                _push(refs, row.get("link_type"), row.get("link_to"))

    for di in _load_jsons("desktop_icons"):
        _push(refs, "Desktop Icon", di.get("name"))
        _push(refs, di.get("link_type"), di.get("link_to"))
        for role in di.get("roles") or []:
            _push(refs, "Role", role.get("role"))

    return refs


def _exists(doctype: str, name: str) -> bool:
    try:
        return bool(frappe.db.exists(doctype, name))
    except Exception:
        return False


@frappe.whitelist()
def validate(write_report: int = 1) -> str:
    """Validate ux/kentender-workspace-configs against live metadata.

    Returns markdown report text; also writes to validation-report.md by default.
    """
    supported = {
        "DocType",
        "Page",
        "Report",
        "Workspace",
        "Workspace Sidebar",
        "Number Card",
        "Dashboard Chart",
        "Desktop Icon",
        "Role",
    }

    refs = _collect_references()
    missing: dict[str, list[str]] = defaultdict(list)
    present_counts: dict[str, dict[str, int]] = {}
    ignored: dict[str, list[str]] = {}

    for ref_type, names in sorted(refs.items()):
        names = sorted(names)
        if ref_type not in supported:
            ignored[ref_type] = names
            continue
        present = 0
        for name in names:
            if _exists(ref_type, name):
                present += 1
            else:
                missing[ref_type].append(name)
        present_counts[ref_type] = {"present": present, "total": len(names)}

    lines: list[str] = []
    lines.append(f"# Workspace Validation ({frappe.local.site})")
    lines.append("")
    lines.append(f"Source: `{_base()}`")
    lines.append("")
    lines.append("## Coverage")
    for ref_type in sorted(present_counts.keys()):
        c = present_counts[ref_type]
        lines.append(f"- {ref_type}: {c['present']}/{c['total']} present")

    if ignored:
        lines.append("")
        lines.append("## Ignored reference types")
        for ref_type, names in sorted(ignored.items()):
            lines.append(f"- {ref_type}: {len(names)} entries")

    lines.append("")
    lines.append("## Missing references")
    any_missing = False
    for ref_type in sorted(missing.keys()):
        if not missing[ref_type]:
            continue
        any_missing = True
        lines.append(f"### {ref_type} ({len(missing[ref_type])})")
        for name in missing[ref_type]:
            lines.append(f"- `{name}`")
        lines.append("")
    if not any_missing:
        lines.append("- None")

    lines.append("")
    lines.append("## Reference counts")
    for ref_type in sorted(refs.keys()):
        lines.append(f"- {ref_type}: {len(refs[ref_type])}")
    report = "\n".join(lines).rstrip() + "\n"

    if int(write_report):
        out = _base() / "validation-report.md"
        out.write_text(report, encoding="utf-8")

    return report
