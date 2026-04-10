# Minimal Golden Testing Scenario

**Procurement of 2 Ultrasound Machines for District Hospitals**

This is intentionally small:

- 1 entity
- 1 department
- 1 budget line
- 1 requisition
- 1 plan item
- 1 tender
- 2 bidders
- 1 winning bid
- 1 contract
- 1 inspection
- 1 GRN
- 2 assets

That is enough to validate the whole chain.

**1\. Master Data**

**Procuring Entity**

- **Code:** MOH
- **Name:** Ministry of Health

**Department**

- **Code:** CLIN-SERV
- **Name:** Clinical Services
- **Entity:** MOH

**Funding Source**

- **Code:** EXCH-DEV
- **Name:** Exchequer Development Grant

**Procurement Category**

- **Code:** MED-EQ
- **Name:** Medical Equipment

**Procurement Method**

- **Code:** ONT
- **Name:** Open National Tender

**Store**

- **Code:** CMS
- **Name:** Central Medical Store
- **Entity:** MOH

**Asset Category**

- **Code:** MED-DIAG
- **Name:** Medical Diagnostic Equipment

**2\. Strategy Data**

**National Framework**

- **Code:** VF2030
- **Name:** Vision 2030

**National Pillar**

- **Code:** SOC
- **Name:** Social Development
- **Framework:** VF2030

**National Objective**

- **Code:** HEALTH-ACCESS
- **Name:** Improve access to healthcare services
- **Pillar:** SOC

**Entity Strategic Plan**

- **Code:** MOH-SP-2026
- **Name:** MOH Strategic Plan 2026–2030
- **Entity:** MOH

**Program**

- **Code:** HD
- **Name:** Healthcare Delivery
- **Strategic Plan:** MOH-SP-2026
- **National Objective:** HEALTH-ACCESS

**Sub-Program**

- **Code:** CRS
- **Name:** County Referral Strengthening
- **Program:** HD

**Output Indicator**

- **Code:** IMG-EQ-HOSP
- **Name:** Number of hospitals equipped with imaging equipment
- **Sub-Program:** CRS

**Performance Target**

- **Code:** PT-IMG-2026
- **Name:** Equip 2 district hospitals with ultrasound machines
- **Indicator:** IMG-EQ-HOSP
- **Target Value:** 2

**3\. Budget Data**

**Budget Control Period**

- **Code:** BCP-2026
- **Fiscal Year:** FY2026/27
- **Entity:** MOH

**Budget**

- **Code:** BUD-MOH-2026-V1
- **Name:** MOH Budget FY2026/27 v1
- **Control Period:** BCP-2026

**Budget Line**

- **Code:** BL-MOH-IMG-001
- **Name:** Diagnostic Imaging Equipment
- **Budget:** BUD-MOH-2026-V1
- **Entity:** MOH
- **Department:** CLIN-SERV
- **Funding Source:** EXCH-DEV
- **Program:** HD
- **Sub-Program:** CRS
- **Indicator:** IMG-EQ-HOSP
- **Target:** PT-IMG-2026
- **Allocated Amount:** 12,000,000
- **Available at start:** 12,000,000

**4\. Test Users**

**Internal**

- requisitioner.test — Department User
- hod.test — Head of Department
- finance.test — Finance Approver
- procurement.test — Procurement Officer
- openingchair.test — Opening Chair
- evaluator.test — Evaluator
- evaluationchair.test — Evaluation Chair
- accounting.test — Accounting Officer
- contractmanager.test — Contract Manager
- inspector.test — Inspection Officer
- storekeeper.test — Storekeeper
- assetofficer.test — Asset Officer

**Suppliers**

- supplier1.test — MedEquip Africa Ltd
- supplier2.test — Afya Diagnostics Ltd

**5\. Transaction Scenario**

**SP1 — Requisition**

**Purchase Requisition**

- **Business ID:** PR-MOH-0001
- **Title:** Procurement of 2 Ultrasound Machines
- **Entity:** MOH
- **Department:** CLIN-SERV
- **Requested By:** requisitioner.test
- **Budget Line:** BL-MOH-IMG-001
- **Program:** HD
- **Sub-Program:** CRS
- **Indicator:** IMG-EQ-HOSP
- **Target:** PT-IMG-2026
- **Priority:** High
- **Requested Amount:** 9,000,000
- **Status at seed:** **Approved**

**Requisition Item**

- **Description:** Portable Ultrasound Machine
- **Quantity:** 2
- **Estimated Unit Cost:** 4,500,000
- **Line Total:** 9,000,000

**Budget Ledger Entry**

- **Type:** Reservation
- **Amount:** 9,000,000
- **Source:** PR-MOH-0001
- **Status:** Posted

**Expected budget position after SP1**

- Allocated: 12,000,000
- Reserved: 9,000,000
- Available: 3,000,000

**SP2 — Procurement Planning**

**Procurement Plan**

- **Business ID:** PP-MOH-0001
- **Title:** MOH Procurement Plan FY2026/27
- **Status at seed:** **Active**

**Procurement Plan Item**

- **Business ID:** PPI-MOH-0001
- **Title:** Procurement of 2 Ultrasound Machines
- **Source Requisition:** PR-MOH-0001
- **Method:** ONT
- **Estimated Amount:** 9,000,000
- **Planned Publication Date:** 2026-07-15
- **Planned Submission Deadline:** 2026-08-01
- **Planned Award Date:** 2026-08-15
- **Status at seed:** **Approved / Ready for Tender**

**Requisition Planning Link**

- **Requisition:** PR-MOH-0001
- **Plan Item:** PPI-MOH-0001
- **Linked Amount:** 9,000,000
- **Status:** Active

**SP3 — Tender + Bids + Opening**

**Tender**

- **Business ID:** TD-MOH-0001
- **Title:** Supply and Delivery of 2 Ultrasound Machines
- **Source Plan Item:** PPI-MOH-0001
- **Method:** ONT
- **Estimated Amount:** 9,000,000
- **Publication Date:** 2026-07-15
- **Submission Deadline:** 2026-08-01 10:00
- **Opening Time:** 2026-08-01 10:30
- **Status at seed:** **Published**

**Tender Criteria**

1.  Tax compliance certificate — Mandatory
2.  Manufacturer authorization — Mandatory
3.  Technical compliance — Score / 70
4.  Financial quote — Score / 30

**Bid 1**

- **Business ID:** BID-TD-0001-01
- **Supplier:** MedEquip Africa Ltd
- **User:** supplier1.test
- **Quoted Amount:** 8,700,000
- **Status at seed:** **Submitted / Locked**

**Bid 2**

- **Business ID:** BID-TD-0001-02
- **Supplier:** Afya Diagnostics Ltd
- **User:** supplier2.test
- **Quoted Amount:** 8,900,000
- **Status at seed:** **Submitted / Locked**

**Opening Session**

- **Business ID:** BOS-MOH-0001
- **Tender:** TD-MOH-0001
- **Chair:** openingchair.test
- **Status at seed:** **Completed**

**Opening Register**

- **Business ID:** BOR-MOH-0001
- **Bids included:** BID-TD-0001-01, BID-TD-0001-02
- **Status:** Locked

**SP4 — Evaluation**

**Evaluation Session**

- **Business ID:** EVS-MOH-0001
- **Tender:** TD-MOH-0001
- **Status at seed:** **Completed**

**Conflict Declaration**

- **Evaluator:** evaluator.test
- **Status:** Declared No Conflict

**Evaluation Results**

**Bid 1**

- Technical Score: 88
- Financial Score: 30
- Combined Score: 91.6

**Bid 2**

- Technical Score: 84
- Financial Score: 29.3
- Combined Score: 87.3

**Evaluation Report**

- **Business ID:** EVR-MOH-0001
- **Recommended Bid:** BID-TD-0001-01
- **Recommended Supplier:** MedEquip Africa Ltd
- **Recommended Amount:** 8,700,000
- **Status at seed:** **Submitted**

**SP5 — Award**

**Award Decision**

- **Business ID:** AWD-MOH-0001
- **Tender:** TD-MOH-0001
- **Recommended Supplier:** MedEquip Africa Ltd
- **Approved Supplier:** MedEquip Africa Ltd
- **Approved Amount:** 8,700,000
- **Status at seed:** **Final Approved**

**Award Notifications**

- Successful notice sent to supplier1.test
- Unsuccessful notice sent to supplier2.test

**Standstill Period**

- **Business ID:** STS-MOH-0001
- **Status at seed:** **Completed**

**SP6 — Contract + Inspection**

**Contract**

- **Business ID:** CT-MOH-0001
- **Award:** AWD-MOH-0001
- **Supplier:** MedEquip Africa Ltd
- **Value:** 8,700,000
- **Status at seed:** **Active**

**Budget Ledger Entry**

- **Type:** Commitment
- **Amount:** 8,700,000
- **Source:** CT-MOH-0001
- **Status:** Posted

**Expected budget position after contract**

- Allocated: 12,000,000
- Reserved: 9,000,000
- Committed: 8,700,000
- Available: according to your service logic, but commitment must be visible and traceable

**Inspection Record**

- **Business ID:** INSP-MOH-0001
- **Contract:** CT-MOH-0001
- **Method:** Mixed
- **Status at seed:** **Completed**

**Inspection Result**

- Machine 1: Pass
- Machine 2: Pass

**Acceptance Record**

- **Business ID:** ACC-MOH-0001
- **Decision:** Accepted
- **Status at seed:** **Accepted**

**SP7 — Stores + Assets**

**Goods Receipt Note**

- **Business ID:** GRN-MOH-0001
- **Contract:** CT-MOH-0001
- **Store:** CMS
- **Quantity Received:** 2
- **Status at seed:** **Posted**

**Store Ledger Entry**

- **Type:** Receipt
- **Quantity:** 2
- **Item:** Portable Ultrasound Machine
- **Store:** CMS

**Assets**

**Asset 1**

- **Business ID:** AST-MOH-0001
- **Name:** Ultrasound Machine Unit 1
- **Source Contract:** CT-MOH-0001
- **Source GRN:** GRN-MOH-0001
- **Assigned To:** District Hospital A
- **Status:** Assigned

**Asset 2**

- **Business ID:** AST-MOH-0002
- **Name:** Ultrasound Machine Unit 2
- **Source Contract:** CT-MOH-0001
- **Source GRN:** GRN-MOH-0001
- **Assigned To:** District Hospital B
- **Status:** Assigned

**6\. Minimal Expected Trace Chain**

From either asset, the trace should be:

AST-MOH-0001  
← GRN-MOH-0001  
← CT-MOH-0001  
← AWD-MOH-0001  
← EVR-MOH-0001  
← EVS-MOH-0001  
← BOS-MOH-0001  
← BID-TD-0001-01  
← TD-MOH-0001  
← PPI-MOH-0001  
← PP-MOH-0001  
← PR-MOH-0001  
← PT-IMG-2026  
← IMG-EQ-HOSP  
← CRS  
← HD  
← MOH-SP-2026  
← HEALTH-ACCESS

**7\. What this scenario is for**

Use this one scenario to test:

**Core happy path**

- requisition
- planning
- tender
- bidding
- opening
- evaluation
- award
- contract
- inspection
- stores
- assets

**Core traceability**

- strategy alignment
- budget movement
- contract linkage
- goods receipt
- asset creation

**Core controls**

- approval chain
- sealed bids
- evaluator scoring
- standstill
- acceptance before stores

**8\. What this scenario is not for**

Do **not** use this first dataset for:

- complaints
- partial acceptance
- failed inspections
- retendering
- multi-lot tenders
- framework contracts
- contract variations

Those should be separate scenarios later.

**9\. Recommendation**

Use this as your **single MVP seed scenario**.

Not 7 packs.  
Not 50 users.  
Not multiple ministries.

Just this.

Then, after this works, add:

- one negative budget scenario
- one failed inspection scenario
- one complaint hold scenario

That is the right sequence.