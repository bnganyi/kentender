from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import frappe


def _ux_base() -> Path:
    app_root = Path(frappe.get_app_path("kentender")).parent
    return app_root / "ux" / "kentender-workspace-configs"


def _iter_docs():
    base = _ux_base()
    for folder in ("workspaces", "sidebars", "desktop_icons"):
        for path in sorted((base / folder).glob("*.json")):
            with path.open(encoding="utf-8") as f:
                payload = json.load(f)
            yield folder, path, payload


def _target_exists(link_type: str, link_to: str, planned: dict[str, set[str]] | None = None) -> bool:
    mapping = {
        "DocType": "DocType",
        "Report": "Report",
        "Page": "Page",
        "Workspace": "Workspace",
        "Workspace Sidebar": "Workspace Sidebar",
    }
    dt = mapping.get((link_type or "").strip())
    if not dt:
        return True
    if planned and link_to in planned.get(dt, set()):
        return True
    return bool(frappe.db.exists(dt, link_to))


def _sanitize_workspace(payload: dict, dropped: list[str], planned: dict[str, set[str]]) -> dict:
    p = deepcopy(payload)

    # Shortcuts
    new_shortcuts = []
    for row in p.get("shortcuts") or []:
        ltype = (row.get("type") or "").strip()
        lto = (row.get("link_to") or "").strip()
        if ltype and lto and not _target_exists(ltype, lto, planned):
            dropped.append(f"Workspace:{p.get('name')} shortcut {ltype}:{lto}")
            continue
        new_shortcuts.append(row)
    p["shortcuts"] = new_shortcuts

    # Links
    new_links = []
    for row in p.get("links") or []:
        if row.get("type") == "Link":
            ltype = (row.get("link_type") or "").strip()
            lto = (row.get("link_to") or "").strip()
            if ltype and lto and not _target_exists(ltype, lto, planned):
                dropped.append(f"Workspace:{p.get('name')} link {ltype}:{lto}")
                continue
        new_links.append(row)
    p["links"] = new_links

    # Quick lists are child rows on Workspace and only depend on document_type.
    new_quick = []
    for row in p.get("quick_lists") or []:
        dt = (row.get("document_type") or "").strip()
        if dt and not frappe.db.exists("DocType", dt):
            dropped.append(f"Workspace:{p.get('name')} quick_list doctype {dt}")
            continue
        new_quick.append(row)
    p["quick_lists"] = new_quick

    # Number cards
    new_cards = []
    for row in p.get("number_cards") or []:
        label = (row.get("number_card_name") or row.get("label") or "").strip()
        if label and not frappe.db.exists("Number Card", label):
            dropped.append(f"Workspace:{p.get('name')} number_card {label}")
            continue
        new_cards.append(row)
    p["number_cards"] = new_cards

    # Charts
    new_charts = []
    for row in p.get("charts") or []:
        label = (row.get("chart_name") or row.get("label") or "").strip()
        if label and not frappe.db.exists("Dashboard Chart", label):
            dropped.append(f"Workspace:{p.get('name')} chart {label}")
            continue
        new_charts.append(row)
    p["charts"] = new_charts

    return p


def _sanitize_sidebar(payload: dict, dropped: list[str], planned: dict[str, set[str]]) -> dict:
    p = deepcopy(payload)
    items = []
    for row in p.get("items") or []:
        if row.get("type") == "Link":
            ltype = (row.get("link_type") or "").strip()
            lto = (row.get("link_to") or "").strip()
            if ltype and lto and not _target_exists(ltype, lto, planned):
                dropped.append(f"Sidebar:{p.get('name')} link {ltype}:{lto}")
                continue
        items.append(row)
    p["items"] = items
    return p


def _sanitize_desktop_icon(payload: dict, dropped: list[str], planned: dict[str, set[str]]) -> dict:
    p = deepcopy(payload)
    ltype = (p.get("link_type") or "").strip()
    lto = (p.get("link_to") or "").strip()
    if ltype and lto and not _target_exists(ltype, lto, planned):
        dropped.append(f"Desktop Icon:{p.get('name')} link {ltype}:{lto}")
        p["hidden"] = 1

    roles = []
    for row in p.get("roles") or []:
        role = (row.get("role") or "").strip()
        if role and not frappe.db.exists("Role", role):
            dropped.append(f"Desktop Icon:{p.get('name')} role {role}")
            continue
        roles.append(row)
    p["roles"] = roles
    return p


@frappe.whitelist()
def sync_ux_workspace_configs(dry_run: int = 1) -> str:
    """Upsert UX workspace/sidebar/desktop icon records from ux/kentender-workspace-configs."""
    dry = bool(int(dry_run))

    created: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []
    dropped_refs: list[str] = []

    items = list(_iter_docs())
    planned: dict[str, set[str]] = {"Workspace": set(), "Workspace Sidebar": set(), "Desktop Icon": set()}
    for _, _, payload in items:
        doctype = (payload.get("doctype") or "").strip()
        name = (payload.get("name") or "").strip()
        if doctype and name:
            planned.setdefault(doctype, set()).add(name)

    for folder, path, payload in items:
        if folder == "workspaces":
            payload = _sanitize_workspace(payload, dropped_refs, planned)
        elif folder == "sidebars":
            payload = _sanitize_sidebar(payload, dropped_refs, planned)
        elif folder == "desktop_icons":
            payload = _sanitize_desktop_icon(payload, dropped_refs, planned)

        doctype = (payload.get("doctype") or "").strip()
        name = (payload.get("name") or "").strip()
        if not doctype or not name:
            skipped.append(f"{path.name} (missing doctype/name)")
            continue

        exists = frappe.db.exists(doctype, name)
        label = f"{doctype}:{name}"
        if exists:
            if dry:
                updated.append(label)
                continue
            doc = frappe.get_doc(doctype, name)
            doc.update(payload)
            doc.save(ignore_permissions=True)
            updated.append(label)
        else:
            if dry:
                created.append(label)
                continue
            doc = frappe.get_doc(payload)
            doc.insert(ignore_permissions=True)
            created.append(label)

    if not dry and (created or updated):
        frappe.db.commit()
        frappe.clear_cache()
        try:
            frappe.utils.install.auto_generate_icons_and_sidebar()
        except Exception:
            pass

    mode = "DRY RUN" if dry else "APPLY"
    lines = [
        f"# KenTender UX Workspace Sync ({mode})",
        "",
        f"Site: `{frappe.local.site}`",
        f"Source: `{_ux_base()}`",
        "",
        "## Summary",
        f"- To create/created: {len(created)}",
        f"- To update/updated: {len(updated)}",
        f"- Skipped: {len(skipped)}",
        f"- Dropped unresolved references: {len(dropped_refs)}",
        "",
        "## Created",
    ]
    if created:
        for v in created:
            lines.append(f"- `{v}`")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Updated")
    if updated:
        for v in updated:
            lines.append(f"- `{v}`")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Skipped")
    if skipped:
        for v in skipped:
            lines.append(f"- {v}")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Dropped unresolved references")
    if dropped_refs:
        for v in dropped_refs:
            lines.append(f"- {v}")
    else:
        lines.append("- None")

    report = "\n".join(lines) + "\n"
    out = Path(frappe.get_app_path("kentender")).parent / "security" / "UX_WORKSPACE_SYNC_REPORT.md"
    out.write_text(report, encoding="utf-8")
    return report
