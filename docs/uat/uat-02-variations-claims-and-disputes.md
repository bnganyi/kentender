# UAT-05: Variations, Claims, Disputes (and FRS 4.16 depth)

## UAT-5 Variation / Claim / Dispute (baseline)
1. Variation validation negative:
   - missing justification should fail
2. Variation positive:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_contract_variation --args "['<CONTRACT>','Cost Adjustment','Scope correction',250]"`
3. Transition variation:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_contract_variation --args "['<VARIATION>','Under Review','procurement review started']"`
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_contract_variation --args "['<VARIATION>','Approved','approved by accounting officer']"`
4. Claim create:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_claim --args "['<CONTRACT>','Supplier','Compensation Claim','Compensation request']"`
5. Claim transition:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_claim --args "['<CLAIM>','Under Review','procurement review']"`
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_claim --args "['<CLAIM>','Approved','liability accepted']"`
6. Dispute create:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_dispute_case --args "['<CONTRACT>','Dispute on valuation']"`
7. Dispute transition:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_dispute_case --args "['<DISPUTE>','In Progress','escalated for hearing']"`
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_dispute_case --args "['<DISPUTE>','Resolved','settlement reached']"`

Expected:
- Variation/claim/dispute transitions follow allowed state graph and role checks
- Audit comments are written for each transition

## Variation governance depth (FRS 4.16): high-impact needs extra approval
Preconditions:
- Set `kentender_variation_high_financial_impact_threshold` (default 1,000,000) low enough for the test, OR use a very large `financial_impact`.
- Second-level approval role: `Head of Finance` (or `kentender_variation_second_level_approval_role`).

1. Create a high-impact `Contract Variation` in `Draft` (do NOT auto-Approved yet):
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_contract_variation --args "['<CONTRACT>','Cost Adjustment','High impact variation',2000000,0,None,None,'Draft',0]"`
2. Move to `Under Review`:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_contract_variation --args "['<VARIATION>','Under Review','procurement review started']"`
3. Attempt to move to `Approved` (should fail because second-level approval is missing):
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_contract_variation --args "['<VARIATION>','Approved','approved by accounting officer']"`
4. Record second-level approval:
   - `bench --site kentender.midas.com execute kentender.kentender.api.second_approve_contract_variation --args "['<VARIATION>','second-level approval by Head of Finance']"`
5. Now attempt `Approved` again (should succeed):
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_contract_variation --args "['<VARIATION>','Approved','approved by accounting officer after second-level approval']"`

