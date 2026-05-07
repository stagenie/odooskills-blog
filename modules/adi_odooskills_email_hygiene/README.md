# adi_odooskills_email_hygiene

Server-side validation of subscriber emails on `/website_mass_mailing/subscribe`.

Rejects: syntax KO, no MX record, disposable domains, role-based local-parts, DNS timeout.

## Architecture

- **Models**
  - `email.validator` (AbstractModel) — stateless logic, 4 sequential validation checks
  - `mailing.contact` — adds `email_status` Selection field (default `'valid'`)
- **Controllers**
  - Override of native `MassMailController.subscribe` — returns FR toast on validation KO
- **Data**
  - `data/disposable_domains.txt` — ~5400 entries from upstream

## Validation Pipeline

The module performs four sequential checks on each email:

1. **Syntax** — Regex against RFC 5322-inspired pattern (covers 99% of real-world emails)
2. **Role-Based** — Reject local-parts like `admin@`, `support@`, `noreply@` (13 terms)
3. **Disposable** — Check against frozenset of ~5400 disposable/temp domain services
4. **MX + DNS** — Query DNS for MX records (3s timeout, module-level cache TTL 1h)

Rejection reasons: `'syntax_ko'`, `'role_based'`, `'disposable'`, `'mx_ko'`, `'dns_timeout'`.

## Refresh disposable list (quarterly)

```bash
cd /home/stadev/vscode-projects/odoo19-dev/addons/odooskills-blog
./tools/refresh_disposable_domains.sh
git diff modules/adi_odooskills_email_hygiene/data/disposable_domains.txt
git commit -m "chore(email-hygiene): refresh disposable list $(date +%Y-%m)"
```

## Run tests

```bash
cd /home/stadev/vscode-projects/odoo19-dev
./odoo/odoo-bin -c config/odoo.conf -d vs19_test_email_hygiene \
  -i adi_odooskills_email_hygiene --test-enable \
  --test-tags adi_odooskills_email_hygiene --stop-after-init
```

Expected: 57 tests, all green.

## Public API

### Single Email Validation

```python
request.env['email.validator'].sudo().validate(email: str) -> (status: str, email_or_none: str | None)
```

- `status` ∈ `{'valid', 'syntax_ko', 'role_based', 'disposable', 'mx_ko', 'dns_timeout'}`
- Returns `(status, email)` if valid, `(status, None)` if rejected

### Batch Validation

```python
request.env['email.validator'].sudo().validate_batch(emails: List[str], progress_every: int = 100) -> List[dict]
```

Example return:
```python
[
    {'email': 'alice@example.com', 'status': 'valid'},
    {'email': 'bob@disposable.co', 'status': 'disposable'},
    {'email': 'admin@acme.fr', 'status': 'role_based'},
]
```

Used by sub-project B (cleanup of legacy contacts).

## RGPD Logging

Rejected emails are logged with the local-part redacted:

```
INFO adi_odooskills_email_hygiene email_status=disposable email=p***@gmail.com remote_ip=1.2.3.4
```

## Dependencies

- `website_mass_mailing` — override of subscribe controller
- `adi_odooskills_geoip` — optional IP geolocation metadata in logs
- `dnspython` — DNS resolver for MX checks

## Changelog

### 19.0.1.0.0 (2026-05-07)
- Initial release
- 4 validation checks: syntax, role-based, disposable, MX+DNS
- MX module-level cache (TTL 1h / 1m on transient errors)
- French toast messages on subscribe rejection
- RGPD-friendly logging with redacted emails
- 57 unit + integration tests (100% coverage of code paths)

## References

- Implementation plan: `docs/superpowers/plans/2026-05-07-email-hygiene-validation.md`
- Design spec: `docs/superpowers/specs/2026-05-07-email-hygiene-validation-design.md`
