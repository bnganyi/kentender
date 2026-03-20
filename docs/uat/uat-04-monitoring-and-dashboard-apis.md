# UAT-08: Monitoring and Dashboard APIs

## UAT-8 Monitoring and Dashboard APIs
1. Generate monthly reports:
   - `bench --site kentender.midas.com execute kentender.kentender.api.create_monthly_contract_monitoring_reports`
2. Check close-out readiness:
   - `bench --site kentender.midas.com execute kentender.kentender.api.get_contract_closeout_readiness --args "['<CONTRACT>']"`
3. Get dashboard:
   - `bench --site kentender.midas.com execute kentender.kentender.api.get_clm_dashboard_summary`

Expected:
- Monthly report rows created
- Readiness returns `ready` plus explicit blockers
- Dashboard returns contract/legal/quality/finance/monitoring aggregates

