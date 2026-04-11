# Minimal Golden — Strategy visibility UAT (Scenario v2)

**Rules:** Test as the named role (not Administrator). Confirm both **can** and **cannot** for each role.

**Scenario reference:** [KenTender Minimal Golden Scenario v2](KenTender%20Minimal%20Golden%20Scenario%20v2.md) (strategy fields on PR: Program HD, Sub-Program CRS, Indicator IMG-EQ-HOSP, Target PT-IMG-2026).

| ID | Role (matrix) | User (golden seed) | Check: sees strategy context | Check: must NOT |
|----|----------------|-------------------|------------------------------|-----------------|
| UAT-001 | Requisitioner | `requisitioner.test@ken-tender.test` | PR shows program / sub-program / indicator / target; amount 9M; 2 items | Approve PR; edit after approval; change strategy linkage when locked |
| UAT-002 | Department Reviewer | (assign per site) | PR visible; strategy context visible | Alter strategy linkage; create procurement plan |
| UAT-003 | Head of Department | `hod.test@ken-tender.test` | Trace + alignment to objective visible | Change national strategy records; create tender |
| UAT-004 | Procurement Planner | `procurement.test@ken-tender.test` | PP/PPI show inherited strategy; method ONT | Override strategy silently |
| UAT-005 | Planning Authority | (matrix role) | Can approve alignment (workflow) | Approve misaligned plan (should be blocked by validation) |
| UAT-006 | Procurement Officer | `procurement.test@ken-tender.test` | Tender shows strategy read-only | Edit strategy master data |

**Workspace / reports (Strategy & Alignment)**

- Open **KenTender Strategy** workspace: **Strategy Alignment Summary** shows non-zero counts when seed is loaded; **Strategy Hierarchy Snapshot** lists MOH chain rows; **Strategy Requisitions By Program** shows PR-MOH-0001 under program HD; **Strategy Linkage Exceptions** is empty for a clean golden seed.

**Sign-off**

- [ ] All rows executed on a site with fresh minimal golden seed.
- [ ] Notes / defects logged with link to `verify_minimal_golden` output.
