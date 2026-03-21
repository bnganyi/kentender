# KenTender ERPNext v16 Workspace Configs

This package contains custom **Workspace**, **Workspace Sidebar**, and **Desktop Icon** JSON configs for the KenTender modules built so far:

- Procurement Planning
- Requisitions
- Suppliers
- Tendering
- Submissions & Opening
- Evaluation & Award
- Contracts & Execution
- Oversight & Audit

## Design approach

These are **custom public workspaces** for ERPNext/Frappe v16, designed around task-oriented navigation rather than raw DocType exposure.

## Package contents

- `workspaces/` - importable Workspace records
- `sidebars/` - v16 Workspace Sidebar records
- `desktop_icons/` - desktop/app-launcher icons linked to sidebars
- `patches/` - optional helper script to upsert records in a custom app

## Recommended install path

1. Review DocType names and report names against your live app.
2. Rename any placeholder Number Cards or Reports to match your actual records.
3. Import into a staging site first using `bench --site <site> import-doc <path-to-json>`.
4. Clear cache and reload Desk after import.
5. Curate sidebar ordering and role restrictions in staging before production.

## Important v16 notes

- v16 uses a persistent sidebar powered by **Workspace Sidebar**.
- Standard workspace modifications can be lost across upgrades; these files are intended as **custom** records.
- Keep cross-module links deliberate, otherwise sidebar context can feel jumpy in v16.

## Placeholder records to create or map

Some blocks reference Number Cards / Reports that may not yet exist in your site, such as:

- `KT Planned APP Value`
- `KT APP Pending Approval`
- `KT Requisition Pending`
- `KT Requisition Commitment Value`
- `KT Active Suppliers`
- `KT Supplier Renewals Due`
- `KT Published Tenders`
- `KT Tenders Closing This Week`
- `KT Tender Submissions Received`
- `KT Late Bids`
- `KT Evaluations Pending`
- `KT Awards Awaiting Approval`
- `KT Contract Handoffs Pending`
- `KT Open Purchase Orders`
- `KT Open Exceptions`
- `KT Open Challenge Cases`

Replace these with your final Number Card names or remove them from the JSON.

## Optional app-based deployment

If you want these in source control, place the JSON records in your app and include them in fixtures or import them through a patch.
