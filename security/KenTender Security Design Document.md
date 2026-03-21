# KenTender Security Design Document

What’s inside:

- global role catalogue
- ERPNext security model and permlevel ladder
- DocPerm template approach
- module-by-module role and permission patterns for Phases 1, 1.5, 2, and 3
- field-level permission allocation by doctype family using permlevel
- workflow authority matrix
- row-level User Permission recommendations
- implementation checklist and common mistakes to avoid

This version is designed as a governance document first, so your team can use it to harden Permission Manager, workflow roles, and field permlevels without improvising role logic mid-build.

# DocPerm matrix and field dictionary workbook

Included sheets:

- Roles_Catalogue
- DocType_Catalogue
- DocPerm_Matrix
- Field_Dictionary
- Workflow_Authority
- User_Permissions
- Page_Report_Roles
- Sources

This is structured around ERPNext/Frappe’s current permission model: DocType permissions by role and permission level, field restriction via permlevel, and row-level restriction via User Permissions.