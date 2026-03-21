# KenTender User Permission Assignment Suggestions (kentender.midas.com)

Source policy: `/home/midasuser/frappe-bench/apps/kentender/security/KenTender_Security_DocPerm_FieldDictionary_CSV_Bundle/User_Permissions.csv`
Output CSV: `/home/midasuser/frappe-bench/apps/kentender/security/USER_PERMISSION_ASSIGNMENTS_SUGGESTED.csv`

## Summary
- Policy rows: 16
- Suggested assignment rows generated: 16
- Rows with no current users for role (placeholders): 0
- Rows with ambiguous allow values (manual for_value required): 13

## Notes
- Placeholder rows have blank `user` and/or `for_value` and must be completed before apply.
- `Administrator` is excluded from auto-suggestions by design.
- Copy vetted rows into `USER_PERMISSION_ASSIGNMENTS_TEMPLATE.csv` before running assignment sync.
