# UAT-09: Retention Release Governance

## UAT-9 Retention Release Governance
1. Negative release attempt while contract is active or DLP not completed:
   - `bench --site kentender.midas.com execute kentender.kentender.api.release_contract_retention --args "['<CONTRACT>',100,'negative test']"`
2. Ensure prerequisites:
   - Contract status is `Closed` or `Terminated`
   - Contract `dlp_status` is `Completed`
   - Retention balance exists
3. Positive partial release:
   - `bench --site kentender.midas.com execute kentender.kentender.api.release_contract_retention --args "['<CONTRACT>',100,'partial release']"`
4. Full release:
   - `bench --site kentender.midas.com execute kentender.kentender.api.release_contract_retention --args "['<CONTRACT>']"`

Expected:
- Release is blocked unless close-out and DLP conditions are met
- Release amount cannot exceed retention balance
- `Retention Ledger` gets `Release` rows with reduced running balance

