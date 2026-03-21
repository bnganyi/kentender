from __future__ import annotations

import csv
import json
from pathlib import Path

import frappe
import frappe.permissions


def _security_bundle_path() -> Path:
    app_root = Path(frappe.get_app_path("kentender")).parent
    return app_root / "security" / "KenTender_Security_DocPerm_FieldDictionary_CSV_Bundle"


def _ux_workspace_config_path() -> Path:
    app_root = Path(frappe.get_app_path("kentender")).parent
    return app_root / "ux" / "kentender-workspace-configs" / "workspaces"


def _read_roles_catalogue() -> list[dict[str, str]]:
    path = _security_bundle_path() / "Roles_Catalogue.csv"
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            role = (row.get("role") or "").strip()
            if role:
                rows.append(row)
    return rows


def _read_docperm_matrix() -> list[dict[str, str]]:
    path = _security_bundle_path() / "DocPerm_Matrix.csv"
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doctype = (row.get("document_type") or "").strip()
            role = (row.get("role") or "").strip()
            if doctype and role:
                rows.append(row)
    return rows


def _read_field_dictionary() -> list[dict[str, str]]:
    path = _security_bundle_path() / "Field_Dictionary.csv"
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doctype = (row.get("document_type") or "").strip()
            fieldname = (row.get("fieldname") or "").strip()
            if doctype and fieldname:
                rows.append(row)
    return rows


def _read_workflow_authority() -> list[dict[str, str]]:
    path = _security_bundle_path() / "Workflow_Authority.csv"
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            family = (row.get("document_type_or_family") or "").strip()
            if family:
                rows.append(row)
    return rows


def _read_user_permissions_csv() -> list[dict[str, str]]:
    path = _security_bundle_path() / "User_Permissions.csv"
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            role = (row.get("role") or "").strip()
            allow = (row.get("allow_doctype") or "").strip()
            if role and allow:
                rows.append(row)
    return rows


def _as_int_flag(value: str | int | None) -> int:
    if value in (None, ""):
        return 0
    if isinstance(value, int):
        return 1 if value else 0
    return 1 if str(value).strip() in {"1", "true", "True", "yes", "Yes"} else 0


@frappe.whitelist()
def sync_roles(dry_run: int = 1) -> str:
    """Create missing roles from Roles_Catalogue.csv.

    Args:
        dry_run: 1 to preview, 0 to apply.
    Returns:
        Markdown summary.
    """
    dry = bool(int(dry_run))
    rows = _read_roles_catalogue()
    expected = sorted({(r.get("role") or "").strip() for r in rows if r.get("role")})

    existing = set(frappe.get_all("Role", pluck="name"))
    missing = [r for r in expected if r not in existing]

    created: list[str] = []
    if not dry:
        for role in missing:
            doc = frappe.get_doc({"doctype": "Role", "role_name": role})
            doc.insert(ignore_permissions=True)
            created.append(role)
        if created:
            frappe.db.commit()

    mode = "DRY RUN" if dry else "APPLY"
    lines = [
        f"# KenTender Security Role Sync ({mode})",
        "",
        f"Site: `{frappe.local.site}`",
        f"Source: `{_security_bundle_path() / 'Roles_Catalogue.csv'}`",
        "",
        "## Summary",
        f"- Expected roles: {len(expected)}",
        f"- Existing roles before sync: {len(existing)}",
        f"- Missing roles: {len(missing)}",
    ]
    if dry:
        lines.append("- Created roles: 0 (dry run)")
    else:
        lines.append(f"- Created roles: {len(created)}")

    lines.append("")
    lines.append("## Missing role names")
    if missing:
        for role in missing:
            lines.append(f"- `{role}`")
    else:
        lines.append("- None")

    return "\n".join(lines) + "\n"


@frappe.whitelist()
def sync_docperms(dry_run: int = 1) -> str:
    """Sync Custom DocPerm rows from DocPerm_Matrix.csv.

    The sync is additive/update-only and does not delete existing DocPerm rows.
    """
    dry = bool(int(dry_run))
    rows = _read_docperm_matrix()
    meta = frappe.get_meta("Custom DocPerm")

    # CSV boolean permission columns we support in Custom DocPerm.
    candidate_fields = [
        "select",
        "read",
        "write",
        "create",
        "delete",
        "submit",
        "cancel",
        "amend",
        "report",
        "export",
        "import",
        "share",
        "print",
        "email",
        "set_user_permissions",
        "mask",
        "apply_user_permissions",
    ]
    perm_fields = [f for f in candidate_fields if meta.has_field(f)]

    roles = set(frappe.get_all("Role", pluck="name"))
    doctypes = set(frappe.get_all("DocType", pluck="name"))

    missing_roles: set[str] = set()
    missing_doctypes: set[str] = set()
    created = 0
    updated = 0
    unchanged = 0
    skipped = 0

    # Deduplicate repeated CSV rows by exact key + last-write-wins.
    desired_rows: dict[tuple[str, str, int, int], dict[str, int | str]] = {}

    for row in rows:
        doctype = (row.get("document_type") or "").strip()
        role = (row.get("role") or "").strip()
        if doctype not in doctypes:
            missing_doctypes.add(doctype)
            skipped += 1
            continue
        if role not in roles:
            missing_roles.add(role)
            skipped += 1
            continue

        permlevel = int((row.get("permlevel") or "0").strip() or "0")
        if_owner = _as_int_flag(row.get("if_owner"))
        key = (doctype, role, permlevel, if_owner)
        payload: dict[str, int | str] = {
            "doctype": doctype,
            "role": role,
            "permlevel": permlevel,
            "if_owner": if_owner,
        }
        for f in perm_fields:
            payload[f] = _as_int_flag(row.get(f))
        desired_rows[key] = payload

    for (doctype, role, permlevel, if_owner), payload in desired_rows.items():
        existing_name = frappe.db.get_value(
            "Custom DocPerm",
            {"parent": doctype, "role": role, "permlevel": permlevel, "if_owner": if_owner},
            "name",
        )

        if not existing_name:
            if dry:
                created += 1
                continue
            frappe.permissions.setup_custom_perms(doctype)
            doc = frappe.get_doc(
                {
                    "doctype": "Custom DocPerm",
                    "parent": doctype,
                    "parenttype": "DocType",
                    "parentfield": "permissions",
                    "role": role,
                    "permlevel": permlevel,
                    "if_owner": if_owner,
                }
            )
            for f in perm_fields:
                setattr(doc, f, int(payload[f]))  # type: ignore[index]
            doc.insert(ignore_permissions=True)
            created += 1
            continue

        doc = frappe.get_doc("Custom DocPerm", existing_name)
        changed = False
        for f in perm_fields:
            desired = int(payload[f])  # type: ignore[index]
            current = int(doc.get(f) or 0)
            if current != desired:
                setattr(doc, f, desired)
                changed = True

        if changed:
            if dry:
                updated += 1
            else:
                doc.save(ignore_permissions=True)
                updated += 1
        else:
            unchanged += 1

    if not dry and (created or updated):
        frappe.db.commit()

    mode = "DRY RUN" if dry else "APPLY"
    lines = [
        f"# KenTender Security DocPerm Sync ({mode})",
        "",
        f"Site: `{frappe.local.site}`",
        f"Source: `{_security_bundle_path() / 'DocPerm_Matrix.csv'}`",
        "",
        "## Summary",
        f"- CSV rows read: {len(rows)}",
        f"- Unique role-doctype-permlevel keys: {len(desired_rows)}",
        f"- Missing roles referenced: {len(missing_roles)}",
        f"- Missing doctypes referenced: {len(missing_doctypes)}",
        f"- Rows skipped due to missing prerequisites: {skipped}",
        f"- To create/created: {created}",
        f"- To update/updated: {updated}",
        f"- Unchanged: {unchanged}",
    ]

    lines.append("")
    lines.append("## Missing roles")
    if missing_roles:
        for role in sorted(missing_roles):
            lines.append(f"- `{role}`")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Missing doctypes")
    if missing_doctypes:
        for dt in sorted(missing_doctypes):
            lines.append(f"- `{dt}`")
    else:
        lines.append("- None")

    report = "\n".join(lines) + "\n"

    # Save latest report for review/history.
    out = _security_bundle_path().parent / "DOCPERM_SYNC_REPORT.md"
    out.write_text(report, encoding="utf-8")
    return report


@frappe.whitelist()
def sync_field_permlevels(dry_run: int = 1) -> str:
    """Align field permlevel from Field_Dictionary.csv for existing fields.

    Additive/update-only for existing Custom Fields and standard fields.
    """
    dry = bool(int(dry_run))
    rows = _read_field_dictionary()

    doctypes = set(frappe.get_all("DocType", pluck="name"))
    missing_doctypes: set[str] = set()
    missing_fields: list[tuple[str, str]] = []
    changed_fields: list[tuple[str, str, int, int]] = []
    unchanged = 0
    skipped = 0

    # last-write-wins for duplicate doctype+fieldname entries
    desired: dict[tuple[str, str], int] = {}
    for row in rows:
        doctype = (row.get("document_type") or "").strip()
        fieldname = (row.get("fieldname") or "").strip()
        if doctype not in doctypes:
            missing_doctypes.add(doctype)
            skipped += 1
            continue
        try:
            permlevel = int((row.get("permlevel") or "0").strip() or "0")
        except Exception:
            permlevel = 0
        desired[(doctype, fieldname)] = permlevel

    for (doctype, fieldname), target in desired.items():
        custom_name = frappe.db.get_value(
            "Custom Field", {"dt": doctype, "fieldname": fieldname}, "name"
        )
        if custom_name:
            doc = frappe.get_doc("Custom Field", custom_name)
            current = int(doc.permlevel or 0)
            if current != target:
                if not dry:
                    doc.permlevel = target
                    doc.save(ignore_permissions=True)
                changed_fields.append((doctype, fieldname, current, target))
            else:
                unchanged += 1
            continue

        std_name = frappe.db.get_value(
            "DocField", {"parent": doctype, "fieldname": fieldname}, "name"
        )
        if std_name:
            doc = frappe.get_doc("DocField", std_name)
            current = int(doc.permlevel or 0)
            if current != target:
                if not dry:
                    doc.permlevel = target
                    doc.save(ignore_permissions=True)
                changed_fields.append((doctype, fieldname, current, target))
            else:
                unchanged += 1
        else:
            missing_fields.append((doctype, fieldname))
            skipped += 1

    if not dry and changed_fields:
        frappe.db.commit()
        # force metadata refresh after field changes
        frappe.clear_cache()

    mode = "DRY RUN" if dry else "APPLY"
    lines = [
        f"# KenTender Security Field Permlevel Sync ({mode})",
        "",
        f"Site: `{frappe.local.site}`",
        f"Source: `{_security_bundle_path() / 'Field_Dictionary.csv'}`",
        "",
        "## Summary",
        f"- CSV rows read: {len(rows)}",
        f"- Unique doctype+field keys: {len(desired)}",
        f"- Missing doctypes referenced: {len(missing_doctypes)}",
        f"- Missing fields referenced: {len(missing_fields)}",
        f"- Rows skipped due to missing prerequisites: {skipped}",
        f"- To change/changed permlevels: {len(changed_fields)}",
        f"- Unchanged: {unchanged}",
    ]

    lines.append("")
    lines.append("## Missing doctypes")
    if missing_doctypes:
        for dt in sorted(missing_doctypes):
            lines.append(f"- `{dt}`")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Missing fields (doctype.fieldname)")
    if missing_fields:
        for doctype, fieldname in sorted(missing_fields):
            lines.append(f"- `{doctype}.{fieldname}`")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Changed field permlevels")
    if changed_fields:
        for doctype, fieldname, current, target in sorted(changed_fields):
            lines.append(f"- `{doctype}.{fieldname}`: {current} -> {target}")
    else:
        lines.append("- None")

    report = "\n".join(lines) + "\n"
    out = _security_bundle_path().parent / "FIELD_PERMLEVEL_SYNC_REPORT.md"
    out.write_text(report, encoding="utf-8")
    return report


def _split_roles(value: str, valid_roles: set[str]) -> set[str]:
    roles = set()
    for part in (value or "").split(","):
        role = part.strip()
        if role in valid_roles:
            roles.add(role)
    return roles


def _expand_doc_family(value: str, valid_doctypes: set[str]) -> list[str]:
    """Map workflow family labels to concrete DocTypes where possible."""
    explicit_map = {
        "Procurement Plan / Plan Item": ["Procurement Plan", "Procurement Plan Item"],
        "Purchase Requisition / Handoff": ["Purchase Requisition", "Requisition Tender Handoff"],
        "Bid Opening Register / Record": ["Bid Opening Register", "Bid Opening Record"],
        "Evaluation Worksheet / Score Record": ["Evaluation Worksheet", "Evaluation Score Record"],
        "Evaluation Consensus / Award Recommendation": [
            "Evaluation Consensus Record",
            "Award Recommendation",
        ],
        "Award Decision / Award Publication": ["Award Decision", "Award Publication Record"],
        "Inspection Report / Acceptance Certificate": ["Inspection Report", "Acceptance Certificate"],
        "Payment Certificate / Invoice Control": ["Payment Certificate", "Invoice Control Record"],
        "Contract Variation / Claim Dispute / Termination": [
            "Contract Variation",
            "Claim Dispute Record",
            "Termination Record",
        ],
    }
    if value in explicit_map:
        return [d for d in explicit_map[value] if d in valid_doctypes]
    return [value] if value in valid_doctypes else []


def _process_state_scope(doctype: str, process: str) -> set[str] | None:
    """Return workflow states relevant to a process label for known doctypes.

    Using scoped states avoids false positives when one CSV row (e.g. final approval)
    is compared against unrelated transitions in the same workflow.
    """
    process = (process or "").strip().lower()

    if doctype == "Procurement Plan":
        if "draft/review" in process:
            return {"Draft", "Department Consolidation", "Procurement Review"}
        if "finance review" in process:
            return {"Finance Review"}
        if "final approval" in process or "publish" in process:
            return {"Submitted", "Approved"}
    if doctype == "Procurement Plan Item":
        if "finance review" in process:
            return {"Under Review"}
    if doctype == "Purchase Requisition":
        if "hod review" in process or "submit" in process:
            return {"Draft", "Submitted", "HoD Review"}
        if "finance / ao review" in process:
            return {"Finance Review", "AO Review"}
        if "procurement readiness" in process:
            return {"Procurement Review"}

    return None


@frappe.whitelist()
def audit_workflow_authority(write_report: int = 1) -> str:
    """Audit workflow transition role authority against Workflow_Authority.csv."""
    rows = _read_workflow_authority()
    valid_roles = set(frappe.get_all("Role", pluck="name"))
    valid_doctypes = set(frappe.get_all("DocType", pluck="name"))

    missing_doctype_refs: list[str] = []
    missing_workflows: list[str] = []
    findings: list[dict] = []

    for row in rows:
        family = (row.get("document_type_or_family") or "").strip()
        process = (row.get("process") or "").strip()
        required = _split_roles((row.get("action_authority") or "").strip(), valid_roles)
        forbidden = _split_roles((row.get("should_not_action") or "").strip(), valid_roles)

        doctypes = _expand_doc_family(family, valid_doctypes)
        if not doctypes:
            missing_doctype_refs.append(family)
            continue

        for dt in doctypes:
            wf_names = frappe.get_all("Workflow", filters={"document_type": dt}, pluck="name")
            if not wf_names:
                missing_workflows.append(dt)
                continue
            for wf in wf_names:
                wf_doc = frappe.get_doc("Workflow", wf)
                scoped_states = _process_state_scope(dt, process)
                scoped_transitions = [
                    t
                    for t in (wf_doc.transitions or [])
                    if t.allowed and (scoped_states is None or t.state in scoped_states)
                ]
                transition_roles = {t.allowed for t in scoped_transitions if t.allowed}
                missing_required = sorted(required - transition_roles)
                present_forbidden = sorted(forbidden & transition_roles)
                findings.append(
                    {
                        "doctype": dt,
                        "workflow": wf,
                        "process": process,
                        "scoped_states": sorted(scoped_states) if scoped_states else [],
                        "required": sorted(required),
                        "transition_roles": sorted(transition_roles),
                        "missing_required": missing_required,
                        "present_forbidden": present_forbidden,
                    }
                )

    findings_with_issues = [
        f for f in findings if f["missing_required"] or f["present_forbidden"]
    ]
    fully_aligned = [
        f for f in findings if not f["missing_required"] and not f["present_forbidden"]
    ]

    lines = [
        f"# KenTender Workflow Authority Audit ({frappe.local.site})",
        "",
        f"Source: `{_security_bundle_path() / 'Workflow_Authority.csv'}`",
        "",
        "## Summary",
        f"- CSV rows read: {len(rows)}",
        f"- Workflow checks performed: {len(findings)}",
        f"- Fully aligned checks: {len(fully_aligned)}",
        f"- Checks with issues: {len(findings_with_issues)}",
        f"- Missing doctype family refs: {len(set(missing_doctype_refs))}",
        f"- Existing doctypes without workflows: {len(set(missing_workflows))}",
        "",
        "## Missing doctype references from CSV",
    ]
    if missing_doctype_refs:
        for family in sorted(set(missing_doctype_refs)):
            lines.append(f"- `{family}`")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Existing doctypes without workflow")
    if missing_workflows:
        for dt in sorted(set(missing_workflows)):
            lines.append(f"- `{dt}`")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Checks with issues")
    if findings_with_issues:
        for f in findings_with_issues:
            lines.append(f"### `{f['doctype']}` / `{f['workflow']}`")
            if f.get("scoped_states"):
                lines.append(f"- State scope: `{', '.join(f['scoped_states'])}`")
            if f["missing_required"]:
                lines.append("- Missing required roles in transitions:")
                for r in f["missing_required"]:
                    lines.append(f"  - `{r}`")
            if f["present_forbidden"]:
                lines.append("- Forbidden roles currently allowed in transitions:")
                for r in f["present_forbidden"]:
                    lines.append(f"  - `{r}`")
            lines.append("")
    else:
        lines.append("- None")

    report = "\n".join(lines).rstrip() + "\n"
    if int(write_report):
        out = _security_bundle_path().parent / "WORKFLOW_AUTHORITY_AUDIT.md"
        out.write_text(report, encoding="utf-8")
    return report


@frappe.whitelist()
def remediate_workflow_authority_phase1(dry_run: int = 1) -> str:
    """Apply conservative workflow transition fixes for currently active workflows.

    Scope is intentionally narrow:
    - Procurement Plan Workflow
    - Purchase Requisition Workflow
    """
    dry = bool(int(dry_run))

    planned = [
        # Ensure Planning Authority chain is represented in APP draft/review flow.
        {
            "workflow": "Procurement Plan Workflow",
            "state": "Draft",
            "action": "Consolidate",
            "next_state": "Department Consolidation",
            "allowed": "Department Planning Officer",
        },
        # Ensure HoP can perform procurement readiness final approval (in addition to Procurement Officer).
        {
            "workflow": "Purchase Requisition Workflow",
            "state": "Procurement Review",
            "action": "Approve Final",
            "next_state": "Approved",
            "allowed": "Head of Procurement",
        },
        # Ensure finance review authority exists for Procurement Plan Item under-review transition.
        {
            "workflow": "Procurement Plan Item Workflow",
            "state": "Under Review",
            "action": "Approve",
            "next_state": "Approved",
            "allowed": "Finance/Budget Officer",
        },
    ]

    existing_roles = set(frappe.get_all("Role", pluck="name"))
    created: list[dict] = []
    skipped_missing_workflow: list[str] = []
    skipped_missing_role: list[str] = []
    skipped_existing: list[dict] = []

    for p in planned:
        if p["allowed"] not in existing_roles:
            skipped_missing_role.append(p["allowed"])
            continue
        if not frappe.db.exists("Workflow", p["workflow"]):
            skipped_missing_workflow.append(p["workflow"])
            continue

        wf = frappe.get_doc("Workflow", p["workflow"])
        exists = False
        for t in (wf.transitions or []):
            if (
                t.state == p["state"]
                and t.action == p["action"]
                and t.next_state == p["next_state"]
                and t.allowed == p["allowed"]
            ):
                exists = True
                break

        if exists:
            skipped_existing.append(p)
            continue

        if not dry:
            wf.append(
                "transitions",
                {
                    "state": p["state"],
                    "action": p["action"],
                    "next_state": p["next_state"],
                    "allowed": p["allowed"],
                },
            )
            wf.save(ignore_permissions=True)
        created.append(p)

    if not dry and created:
        frappe.db.commit()
        frappe.clear_cache()

    mode = "DRY RUN" if dry else "APPLY"
    lines = [
        f"# KenTender Workflow Authority Remediation ({mode})",
        "",
        f"Site: `{frappe.local.site}`",
        "",
        "## Summary",
        f"- Planned transition additions: {len(planned)}",
        f"- To create/created: {len(created)}",
        f"- Already present: {len(skipped_existing)}",
        f"- Skipped (missing workflow): {len(set(skipped_missing_workflow))}",
        f"- Skipped (missing role): {len(set(skipped_missing_role))}",
    ]

    lines.append("")
    lines.append("## Transition additions")
    if created:
        for p in created:
            lines.append(
                f"- `{p['workflow']}`: `{p['state']}` --`{p['action']}`--> `{p['next_state']}` as `{p['allowed']}`"
            )
    else:
        lines.append("- None")

    if skipped_existing:
        lines.append("")
        lines.append("## Already present")
        for p in skipped_existing:
            lines.append(
                f"- `{p['workflow']}`: `{p['state']}` --`{p['action']}`--> `{p['next_state']}` as `{p['allowed']}`"
            )

    if skipped_missing_workflow:
        lines.append("")
        lines.append("## Missing workflows")
        for wf in sorted(set(skipped_missing_workflow)):
            lines.append(f"- `{wf}`")

    if skipped_missing_role:
        lines.append("")
        lines.append("## Missing roles")
        for role in sorted(set(skipped_missing_role)):
            lines.append(f"- `{role}`")

    report = "\n".join(lines) + "\n"
    out = _security_bundle_path().parent / "WORKFLOW_AUTHORITY_REMEDIATION.md"
    out.write_text(report, encoding="utf-8")
    return report


@frappe.whitelist()
def audit_user_permission_baseline(write_report: int = 1) -> str:
    """Audit User_Permissions.csv readiness against live metadata.

    This does not create User Permission rows (CSV has policy guidance, not concrete user/value assignments).
    """
    rows = _read_user_permissions_csv()
    roles = set(frappe.get_all("Role", pluck="name"))
    doctypes = set(frappe.get_all("DocType", pluck="name"))

    missing_roles: set[str] = set()
    missing_doctypes: set[str] = set()
    value_counts: dict[str, int] = {}
    role_user_counts: dict[str, int] = {}
    applicable_doctypes_missing: set[str] = set()

    seen_roles = sorted({(r.get("role") or "").strip() for r in rows})
    for role in seen_roles:
        role_user_counts[role] = len(
            frappe.get_all("Has Role", filters={"role": role}, distinct=True, pluck="parent")
        )

    for row in rows:
        role = (row.get("role") or "").strip()
        allow = (row.get("allow_doctype") or "").strip()
        applicable = (row.get("recommended_applicable_for") or "").strip()

        if role not in roles:
            missing_roles.add(role)
        if allow not in doctypes:
            missing_doctypes.add(allow)
        else:
            if allow not in value_counts:
                try:
                    value_counts[allow] = len(frappe.get_all(allow, pluck="name", limit=100000))
                except Exception:
                    value_counts[allow] = -1

        if applicable:
            for part in applicable.replace('"', "").split(";"):
                for dt in [p.strip() for p in part.split(",") if p.strip()]:
                    if dt not in doctypes:
                        applicable_doctypes_missing.add(dt)

    ready_rows = 0
    blocked_rows = 0
    for row in rows:
        role = (row.get("role") or "").strip()
        allow = (row.get("allow_doctype") or "").strip()
        if role in roles and allow in doctypes:
            ready_rows += 1
        else:
            blocked_rows += 1

    lines = [
        f"# KenTender User Permission Baseline Audit ({frappe.local.site})",
        "",
        f"Source: `{_security_bundle_path() / 'User_Permissions.csv'}`",
        "",
        "## Summary",
        f"- CSV policy rows: {len(rows)}",
        f"- Ready policy rows (role+allow doctype exist): {ready_rows}",
        f"- Blocked policy rows (missing role/doctype): {blocked_rows}",
        f"- Missing roles: {len(missing_roles)}",
        f"- Missing allow doctypes: {len(missing_doctypes)}",
        f"- Missing 'recommended_applicable_for' doctypes: {len(applicable_doctypes_missing)}",
        "",
        "## Role assignment readiness (users per role)",
    ]
    for role in sorted(role_user_counts):
        lines.append(f"- `{role}`: {role_user_counts[role]} users")

    lines.append("")
    lines.append("## Allow doctypes and available record counts")
    for allow in sorted(value_counts):
        count = value_counts[allow]
        if count >= 0:
            lines.append(f"- `{allow}`: {count} records")
        else:
            lines.append(f"- `{allow}`: unable to count")

    lines.append("")
    lines.append("## Missing roles")
    if missing_roles:
        for role in sorted(missing_roles):
            lines.append(f"- `{role}`")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Missing allow doctypes")
    if missing_doctypes:
        for dt in sorted(missing_doctypes):
            lines.append(f"- `{dt}`")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Missing recommended_applicable_for doctypes")
    if applicable_doctypes_missing:
        for dt in sorted(applicable_doctypes_missing):
            lines.append(f"- `{dt}`")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Next action")
    lines.append(
        "- Generate explicit assignments (user, allow, for_value) per active role; this CSV is policy-level and cannot be auto-applied without concrete values."
    )

    report = "\n".join(lines) + "\n"
    sec_dir = _security_bundle_path().parent
    if int(write_report):
        (sec_dir / "USER_PERMISSION_BASELINE_AUDIT.md").write_text(report, encoding="utf-8")

        # Write assignment template for controlled manual completion/import.
        template = "\n".join(
            [
                "user,role,allow,for_value,applicable_for,hide_descendants,is_default,apply_to_all_doctypes",
                "# example@example.com,Procurement Officer,Company,My Company,,,,",
            ]
        ) + "\n"
        (sec_dir / "USER_PERMISSION_ASSIGNMENTS_TEMPLATE.csv").write_text(
            template, encoding="utf-8"
        )
    return report


def _read_user_permission_assignments() -> list[dict[str, str]]:
    path = _security_bundle_path().parent / "USER_PERMISSION_ASSIGNMENTS_TEMPLATE.csv"
    rows: list[dict[str, str]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            user = (row.get("user") or "").strip()
            allow = (row.get("allow") or "").strip()
            for_value = (row.get("for_value") or "").strip()
            if user and allow and for_value and not user.startswith("#"):
                rows.append(row)
    return rows


@frappe.whitelist()
def generate_user_permission_assignment_suggestions(write_report: int = 1) -> str:
    """Generate starter assignment CSV from policy + current user roles.

    Output:
    - security/USER_PERMISSION_ASSIGNMENTS_SUGGESTED.csv
    - security/USER_PERMISSION_ASSIGNMENT_SUGGESTION_REPORT.md
    """
    policy_rows = _read_user_permissions_csv()
    users = set(frappe.get_all("User", pluck="name"))
    doctypes = set(frappe.get_all("DocType", pluck="name"))

    # role -> users
    role_users: dict[str, list[str]] = {}
    for row in policy_rows:
        role = (row.get("role") or "").strip()
        if role in role_users:
            continue
        role_users[role] = sorted(
            u
            for u in frappe.get_all("Has Role", filters={"role": role}, distinct=True, pluck="parent")
            if u in users and u != "Administrator"
        )

    # cache doctype names for allow values
    dt_values: dict[str, list[str]] = {}
    for row in policy_rows:
        allow = (row.get("allow_doctype") or "").strip()
        if allow in dt_values or allow not in doctypes:
            continue
        try:
            dt_values[allow] = sorted(frappe.get_all(allow, pluck="name", limit=100000))
        except Exception:
            dt_values[allow] = []

    suggested_lines = [
        "user,role,allow,for_value,applicable_for,hide_descendants,is_default,apply_to_all_doctypes"
    ]
    suggested_count = 0
    empty_role_rows = 0
    ambiguous_value_rows = 0

    for row in policy_rows:
        role = (row.get("role") or "").strip()
        allow = (row.get("allow_doctype") or "").strip()
        # Keep this blank in starter rows; policy text is not always a valid DocType.
        applicable_for = ""
        values = dt_values.get(allow, [])
        role_members = role_users.get(role, [])

        # Choose best-effort default value:
        # - single record => use it
        # - else blank for manual completion
        for_value = values[0] if len(values) == 1 else ""
        if len(values) > 1:
            ambiguous_value_rows += 1

        if not role_members:
            empty_role_rows += 1
            # Keep a placeholder row so implementers can assign users later.
            suggested_lines.append(f",{role},{allow},{for_value},{applicable_for},0,0,0")
            suggested_count += 1
            continue

        for user in role_members:
            suggested_lines.append(
                f"{user},{role},{allow},{for_value},{applicable_for},0,0,0"
            )
            suggested_count += 1

    sec_dir = _security_bundle_path().parent
    suggested_path = sec_dir / "USER_PERMISSION_ASSIGNMENTS_SUGGESTED.csv"
    suggested_path.write_text("\n".join(suggested_lines) + "\n", encoding="utf-8")

    lines = [
        f"# KenTender User Permission Assignment Suggestions ({frappe.local.site})",
        "",
        f"Source policy: `{_security_bundle_path() / 'User_Permissions.csv'}`",
        f"Output CSV: `{suggested_path}`",
        "",
        "## Summary",
        f"- Policy rows: {len(policy_rows)}",
        f"- Suggested assignment rows generated: {suggested_count}",
        f"- Rows with no current users for role (placeholders): {empty_role_rows}",
        f"- Rows with ambiguous allow values (manual for_value required): {ambiguous_value_rows}",
        "",
        "## Notes",
        "- Placeholder rows have blank `user` and/or `for_value` and must be completed before apply.",
        "- `Administrator` is excluded from auto-suggestions by design.",
        "- Copy vetted rows into `USER_PERMISSION_ASSIGNMENTS_TEMPLATE.csv` before running assignment sync.",
    ]
    report = "\n".join(lines) + "\n"

    if int(write_report):
        (sec_dir / "USER_PERMISSION_ASSIGNMENT_SUGGESTION_REPORT.md").write_text(
            report, encoding="utf-8"
        )
    return report


@frappe.whitelist()
def export_user_role_roster(write_report: int = 1) -> str:
    """Export non-admin active users and their current roles."""
    users = frappe.get_all(
        "User",
        filters={"enabled": 1},
        fields=["name", "full_name", "user_type"],
        order_by="name asc",
    )

    rows: list[tuple[str, str, str, str]] = []
    for u in users:
        user = u.name
        if user in {"Administrator", "Guest"}:
            continue
        roles = sorted(
            r
            for r in frappe.get_all("Has Role", filters={"parent": user}, pluck="role")
            if r not in {"All", "Guest"}
        )
        rows.append((user, u.full_name or "", u.user_type or "", "; ".join(roles)))

    sec_dir = _security_bundle_path().parent
    csv_lines = ["user,full_name,user_type,current_roles"]
    for user, full_name, user_type, role_list in rows:
        # basic CSV escaping for commas/quotes
        def esc(v: str) -> str:
            v = v.replace('"', '""')
            return f'"{v}"'

        csv_lines.append(",".join([esc(user), esc(full_name), esc(user_type), esc(role_list)]))

    out_csv = sec_dir / "USER_ROLE_ROSTER.csv"
    out_csv.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")

    lines = [
        f"# KenTender User Role Roster ({frappe.local.site})",
        "",
        f"Output CSV: `{out_csv}`",
        "",
        "## Summary",
        f"- Active users exported (excluding Administrator/Guest): {len(rows)}",
        "",
        "## Notes",
        "- Use this roster to assign new KenTender roles before applying row-level User Permissions.",
        "- After role assignment, re-run suggestion generation and assignment dry run.",
    ]
    report = "\n".join(lines) + "\n"
    if int(write_report):
        (sec_dir / "USER_ROLE_ROSTER_REPORT.md").write_text(report, encoding="utf-8")
    return report


def _test_user_plan() -> list[dict]:
    """Persona users for test/UAT security validation."""
    return [
        {
            "email": "planner.test@kentender.local",
            "first_name": "Planning",
            "last_name": "Officer",
            "roles": ["Planning Authority", "Department Planning Officer", "Procurement Planner"],
        },
        {
            "email": "requestor.test@kentender.local",
            "first_name": "Requestor",
            "last_name": "User",
            "roles": ["Requestor", "Head of Department"],
        },
        {
            "email": "finance.test@kentender.local",
            "first_name": "Finance",
            "last_name": "Officer",
            "roles": ["Finance/Budget Officer", "Accounting Officer", "Accounts Payable Officer"],
        },
        {
            "email": "procurement.test@kentender.local",
            "first_name": "Procurement",
            "last_name": "Officer",
            "roles": ["Procurement Officer", "Head of Procurement", "Tender Committee Secretary"],
        },
        {
            "email": "supplierreg.test@kentender.local",
            "first_name": "Supplier",
            "last_name": "Registrar",
            "roles": ["Supplier Registration Officer"],
        },
        {
            "email": "opening.test@kentender.local",
            "first_name": "Opening",
            "last_name": "Committee",
            "roles": ["Opening Committee Member"],
        },
        {
            "email": "evaluator.test@kentender.local",
            "first_name": "Evaluation",
            "last_name": "Committee",
            "roles": ["Evaluation Committee Member", "Evaluation Committee Chair"],
        },
        {
            "email": "contracts.test@kentender.local",
            "first_name": "Contracts",
            "last_name": "Manager",
            "roles": ["Contract Manager", "Inspection & Acceptance Officer"],
        },
        {
            "email": "audit.test@kentender.local",
            "first_name": "Internal",
            "last_name": "Audit",
            "roles": ["Internal Auditor", "Oversight Viewer"],
        },
        {
            "email": "supplier.portal.test@kentender.local",
            "first_name": "Supplier",
            "last_name": "Bidder",
            "roles": ["Supplier Bidder User"],
            "user_type": "Website User",
        },
    ]


@frappe.whitelist()
def provision_test_security_users(dry_run: int = 1, default_password: str = "Admin@123") -> str:
    """Create/align test users and assign KenTender security roles."""
    dry = bool(int(dry_run))
    plan = _test_user_plan()
    roles = set(frappe.get_all("Role", pluck="name"))
    existing_users = set(frappe.get_all("User", pluck="name"))

    created_users: list[str] = []
    updated_users: list[str] = []
    missing_roles: set[str] = set()
    assigned_roles: list[tuple[str, str]] = []
    already_had_roles: list[tuple[str, str]] = []

    for entry in plan:
        email = entry["email"]
        first_name = entry["first_name"]
        last_name = entry["last_name"]
        user_type = entry.get("user_type", "System User")
        desired_roles = [r for r in entry["roles"] if r in roles]
        for r in entry["roles"]:
            if r not in roles:
                missing_roles.add(r)

        if email not in existing_users:
            if not dry:
                doc = frappe.get_doc(
                    {
                        "doctype": "User",
                        "email": email,
                        "first_name": first_name,
                        "last_name": last_name,
                        "enabled": 1,
                        "user_type": user_type,
                        "send_welcome_email": 0,
                    }
                )
                doc.insert(ignore_permissions=True)
                doc.new_password = default_password
                doc.save(ignore_permissions=True)
            created_users.append(email)
        else:
            if not dry:
                doc = frappe.get_doc("User", email)
                changed = False
                if not doc.enabled:
                    doc.enabled = 1
                    changed = True
                if doc.user_type != user_type:
                    doc.user_type = user_type
                    changed = True
                if changed:
                    doc.save(ignore_permissions=True)
                    updated_users.append(email)

        # role assignment
        current_roles = set(
            frappe.get_all("Has Role", filters={"parent": email}, pluck="role")
        ) if (email in existing_users or not dry) else set()

        for role in desired_roles:
            if role in current_roles:
                already_had_roles.append((email, role))
                continue
            if not dry:
                u = frappe.get_doc("User", email)
                u.add_roles(role)
            assigned_roles.append((email, role))

    if not dry and (created_users or updated_users or assigned_roles):
        frappe.db.commit()
        frappe.clear_cache()

    mode = "DRY RUN" if dry else "APPLY"
    lines = [
        f"# KenTender Test User Provisioning ({mode})",
        "",
        f"Site: `{frappe.local.site}`",
        "",
        "## Summary",
        f"- Planned persona users: {len(plan)}",
        f"- To create/created users: {len(created_users)}",
        f"- Updated existing users: {len(updated_users)}",
        f"- To assign/assigned role links: {len(assigned_roles)}",
        f"- Already had role links: {len(already_had_roles)}",
        f"- Missing roles in site: {len(missing_roles)}",
    ]
    if not dry:
        lines.append(f"- Default password set for newly created users: `{default_password}`")

    lines.append("")
    lines.append("## Created users")
    if created_users:
        for u in created_users:
            lines.append(f"- `{u}`")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Assigned role links")
    if assigned_roles:
        for user, role in assigned_roles:
            lines.append(f"- `{user}` -> `{role}`")
    else:
        lines.append("- None")

    if missing_roles:
        lines.append("")
        lines.append("## Missing roles")
        for role in sorted(missing_roles):
            lines.append(f"- `{role}`")

    report = "\n".join(lines) + "\n"
    sec_dir = _security_bundle_path().parent
    (sec_dir / "TEST_USER_PROVISIONING_REPORT.md").write_text(report, encoding="utf-8")
    return report


@frappe.whitelist()
def apply_user_permission_assignments(dry_run: int = 1) -> str:
    """Apply concrete User Permission assignments from template CSV.

    Expected columns:
    user,role,allow,for_value,applicable_for,hide_descendants,is_default,apply_to_all_doctypes
    """
    dry = bool(int(dry_run))
    rows = _read_user_permission_assignments()

    users = set(frappe.get_all("User", pluck="name"))
    roles = set(frappe.get_all("Role", pluck="name"))
    doctypes = set(frappe.get_all("DocType", pluck="name"))

    created = 0
    existing = 0
    skipped = 0
    missing_users: set[str] = set()
    missing_roles: set[str] = set()
    missing_doctypes: set[str] = set()
    missing_values: list[tuple[str, str]] = []

    for row in rows:
        user = (row.get("user") or "").strip()
        role = (row.get("role") or "").strip()
        allow = (row.get("allow") or "").strip()
        for_value = (row.get("for_value") or "").strip()
        applicable_for = (row.get("applicable_for") or "").strip() or None
        hide_descendants = _as_int_flag(row.get("hide_descendants"))
        is_default = _as_int_flag(row.get("is_default"))
        apply_to_all = _as_int_flag(row.get("apply_to_all_doctypes"))

        if user not in users:
            missing_users.add(user)
            skipped += 1
            continue
        if role and role not in roles:
            missing_roles.add(role)
            skipped += 1
            continue
        if allow not in doctypes:
            missing_doctypes.add(allow)
            skipped += 1
            continue
        if applicable_for and applicable_for not in doctypes:
            missing_doctypes.add(applicable_for)
            skipped += 1
            continue
        if not frappe.db.exists(allow, for_value):
            missing_values.append((allow, for_value))
            skipped += 1
            continue

        # Optional guard: if role provided, ensure user has it.
        if role:
            has_role = frappe.db.exists("Has Role", {"parent": user, "role": role})
            if not has_role:
                skipped += 1
                continue

        filters = {
            "user": user,
            "allow": allow,
            "for_value": for_value,
            "applicable_for": applicable_for,
        }
        existing_name = frappe.db.get_value("User Permission", filters, "name")
        if existing_name:
            existing += 1
            continue

        if not dry:
            doc = frappe.get_doc(
                {
                    "doctype": "User Permission",
                    "user": user,
                    "allow": allow,
                    "for_value": for_value,
                    "applicable_for": applicable_for,
                    "hide_descendants": hide_descendants,
                    "is_default": is_default,
                    "apply_to_all_doctypes": apply_to_all,
                }
            )
            doc.insert(ignore_permissions=True)
        created += 1

    if not dry and created:
        frappe.db.commit()
        frappe.clear_cache()

    mode = "DRY RUN" if dry else "APPLY"
    lines = [
        f"# KenTender User Permission Assignment Sync ({mode})",
        "",
        f"Site: `{frappe.local.site}`",
        f"Source: `{_security_bundle_path().parent / 'USER_PERMISSION_ASSIGNMENTS_TEMPLATE.csv'}`",
        "",
        "## Summary",
        f"- Assignment rows read: {len(rows)}",
        f"- To create/created: {created}",
        f"- Already existing: {existing}",
        f"- Skipped: {skipped}",
        f"- Missing users: {len(missing_users)}",
        f"- Missing roles: {len(missing_roles)}",
        f"- Missing doctypes: {len(missing_doctypes)}",
        f"- Missing allow values: {len(missing_values)}",
    ]

    lines.append("")
    lines.append("## Missing users")
    if missing_users:
        for v in sorted(missing_users):
            lines.append(f"- `{v}`")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Missing roles")
    if missing_roles:
        for v in sorted(missing_roles):
            lines.append(f"- `{v}`")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Missing doctypes")
    if missing_doctypes:
        for v in sorted(missing_doctypes):
            lines.append(f"- `{v}`")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Missing allow values (allow.for_value)")
    if missing_values:
        for allow, val in sorted(set(missing_values)):
            lines.append(f"- `{allow}.{val}`")
    else:
        lines.append("- None")

    report = "\n".join(lines) + "\n"
    out = _security_bundle_path().parent / "USER_PERMISSION_ASSIGNMENT_SYNC_REPORT.md"
    out.write_text(report, encoding="utf-8")
    return report


@frappe.whitelist()
def seed_ux_workspace_placeholders(dry_run: int = 1) -> str:
    """Create missing Number Cards and Report placeholders referenced by UX configs."""
    dry = bool(int(dry_run))
    ws_base = _ux_workspace_config_path()

    number_cards: set[str] = set()
    reports: set[str] = set()
    source_files = sorted(ws_base.glob("*.json"))
    for path in source_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload.get("number_cards") or []:
            card = (row.get("number_card_name") or row.get("label") or "").strip()
            if card:
                number_cards.add(card)

        for row in payload.get("shortcuts") or []:
            ltype = (row.get("type") or "").strip()
            lto = (row.get("link_to") or "").strip()
            if ltype == "Report" and lto:
                reports.add(lto)

        for row in payload.get("links") or []:
            if row.get("type") != "Link":
                continue
            ltype = (row.get("link_type") or "").strip()
            lto = (row.get("link_to") or "").strip()
            if ltype == "Report" and lto:
                reports.add(lto)

    created_cards = 0
    existing_cards = 0
    created_reports = 0
    existing_reports = 0
    skipped_reports: list[str] = []

    for card_name in sorted(number_cards):
        if frappe.db.exists("Number Card", card_name):
            existing_cards += 1
            continue
        created_cards += 1
        if dry:
            continue
        frappe.get_doc(
            {
                "doctype": "Number Card",
                "label": card_name,
                "type": "Document Type",
                "function": "Count",
                "document_type": "ToDo",
                "is_public": 1,
                "module": "KenTender",
            }
        ).insert(ignore_permissions=True)

    ref_doctype = "Purchase Requisition" if frappe.db.exists("DocType", "Purchase Requisition") else "DocType"
    for report_name in sorted(reports):
        if frappe.db.exists("Report", report_name):
            existing_reports += 1
            continue
        created_reports += 1
        if dry:
            continue
        try:
            frappe.get_doc(
                {
                    "doctype": "Report",
                    "report_name": report_name,
                    "ref_doctype": ref_doctype,
                    "report_type": "Script Report",
                    "is_standard": "No",
                    "module": "KenTender",
                }
            ).insert(ignore_permissions=True)
        except Exception:
            skipped_reports.append(report_name)

    if not dry and (created_cards or created_reports):
        frappe.db.commit()
        frappe.clear_cache()

    mode = "DRY RUN" if dry else "APPLY"
    lines = [
        f"# KenTender UX Placeholder Seed ({mode})",
        "",
        f"Site: `{frappe.local.site}`",
        f"Source: `{ws_base}`",
        "",
        "## Number Cards",
        f"- Referenced: {len(number_cards)}",
        f"- Existing: {existing_cards}",
        f"- To create/created: {created_cards}",
        "",
        "## Reports",
        f"- Referenced: {len(reports)}",
        f"- Existing: {existing_reports}",
        f"- To create/created: {created_reports}",
        f"- Insert skipped (validation): {len(skipped_reports)}",
    ]

    if skipped_reports:
        lines.append("")
        lines.append("## Skipped Reports")
        for name in skipped_reports:
            lines.append(f"- `{name}`")

    report = "\n".join(lines) + "\n"
    out = _security_bundle_path().parent / "UX_PLACEHOLDER_SEED_REPORT.md"
    out.write_text(report, encoding="utf-8")
    return report


@frappe.whitelist()
def create_missing_ux_doctypes(dry_run: int = 1) -> str:
    """Create missing UX-referenced DocType placeholders for staged rollout."""
    dry = bool(int(dry_run))
    target_doctypes = [
        "Approval Matrix Rule",
        "Award PO Handoff",
        "Award Publication Record",
        "Bid Opening Register",
        "Bid Receipt Log",
        "Budget Control Rule",
        "Exception Register Entry",
        "Post Qualification Check",
        "Supplier Bank Detail",
        "Supplier Beneficial Ownership",
        "Supplier Performance Baseline",
        "Supplier Renewal Review",
        "Tender Eligibility Rule",
        "Tender Evaluation Scheme",
        "Tender Security Rule",
        "Tender Submission Attachment",
        "Tender Submission Lot Response",
    ]

    created = 0
    existing = 0
    failed: list[str] = []
    module_name = "KenTender"

    for dt in target_doctypes:
        if frappe.db.exists("DocType", dt):
            existing += 1
            continue

        created += 1
        if dry:
            continue

        try:
            doc = frappe.get_doc(
                {
                    "doctype": "DocType",
                    "name": dt,
                    "module": module_name,
                    "custom": 1,
                    "istable": 0,
                    "is_submittable": 0,
                    "track_changes": 1,
                    "autoname": "hash",
                    "engine": "InnoDB",
                    "fields": [
                        {
                            "fieldname": "title",
                            "label": "Title",
                            "fieldtype": "Data",
                            "reqd": 1,
                            "in_list_view": 1,
                        }
                    ],
                    "permissions": [
                        {
                            "role": "System Manager",
                            "read": 1,
                            "write": 1,
                            "create": 1,
                            "delete": 1,
                            "report": 1,
                            "export": 1,
                            "share": 1,
                            "print": 1,
                            "email": 1,
                        }
                    ],
                }
            )
            doc.insert(ignore_permissions=True)
        except Exception:
            failed.append(dt)

    if not dry and created:
        frappe.db.commit()
        frappe.clear_cache()

    mode = "DRY RUN" if dry else "APPLY"
    lines = [
        f"# KenTender Missing UX DocTypes ({mode})",
        "",
        f"Site: `{frappe.local.site}`",
        "",
        "## Summary",
        f"- Target DocTypes: {len(target_doctypes)}",
        f"- Already existing: {existing}",
        f"- To create/created: {created}",
        f"- Failed inserts: {len(failed)}",
    ]

    if failed:
        lines.append("")
        lines.append("## Failed")
        for dt in failed:
            lines.append(f"- `{dt}`")

    report = "\n".join(lines) + "\n"
    out = _security_bundle_path().parent / "MISSING_UX_DOCTYPES_REPORT.md"
    out.write_text(report, encoding="utf-8")
    return report
