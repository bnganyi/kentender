# KenTender external signature adapter (FRS 4.2)

Contracts support **`signature_mode` = Role Based** (flags only, no token) or **External Verified** (token verified via an optional site hook).

## Site configuration (`site_config.json`)

| Key | Purpose |
|-----|---------|
| `kentender_signature_verifier` | Dotted path to a Python callable that verifies the signer’s token. |
| `kentender_signature_strict` | If `true`, **External Verified** signing **must** use a configured verifier (no SHA-256 token fallback). |

Example:

```json
{
  "kentender_signature_verifier": "my_integrations.signing.verify_ken_tender_signature",
  "kentender_signature_strict": true
}
```

## Verifier callable

KenTender calls your function with:

- `contract_name` (str)
- `signer_role` (str): `"Supplier"` or `"Accounting Officer"`
- `token` (str): opaque token from the client (e.g. IdP / e-sign provider callback payload)
- `user` (str): logged-in Frappe user
- `contract` (dict, optional): `contract.as_dict()` — if your function does not accept this argument, KenTender retries without it.

**Return value** (required): a `dict` with:

- `ok` (bool): `True` if verification succeeded
- `signature_hash` (str): stable hash or digest to store on the Contract (provider-specific or content digest)

**Optional** (stored on Contract when present):

- `provider` (str)
- `signer_certificate_subject` (str)
- `signer_certificate_serial` (str)
- `verification_reference` (str): provider audit / transaction id
- `signed_at` (datetime or ISO string): provider timestamp; else KenTender uses server time

## API

- **`sign_contract(contract_name, signer_role, signature_token=..., signature_provider=...)`**  
  In **External Verified** mode, `signature_token` is mandatory (unless you extend the flow).
- **`get_signature_integration_status()`** (System Manager only): returns whether a verifier is configured and if strict mode is on.

## Operational notes

- **Role Based** mode ignores tokens; use for pilots without an e-sign stack.
- Without `kentender_signature_verifier` and without **strict** mode, External Verified uses a **development fallback** (SHA-256 of token, min length 12). Do **not** rely on this for non-repudiation.
- Set **`kentender_signature_strict`: true** in production when External Verified contracts must not activate without a real verifier.
