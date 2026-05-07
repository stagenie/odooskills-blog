import logging
import re

from odoo import api, models

_logger = logging.getLogger(__name__)

# Regex covers ~99% of real-world emails. Strict RFC 5322 cannot be expressed
# as a single regex; this rejects obvious garbage and accepts standard atoms.
_EMAIL_RE = re.compile(
    r"^(?P<local>[A-Z0-9._%+\-]+)"
    r"@(?P<domain>(?:[A-Z0-9](?:[A-Z0-9\-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,})$",
    re.IGNORECASE,
)

INVALID_TLDS = frozenset({'test', 'invalid', 'localhost', 'example'})

ROLE_BASED_LOCAL_PARTS = frozenset({
    'admin', 'administrator', 'contact', 'hello', 'help', 'hr', 'info',
    'jobs', 'mail', 'marketing', 'no-reply', 'noreply', 'office',
    'postmaster', 'sales', 'support',
})


def _normalize_email(email):
    """ lowercase + strip + idna-encode the domain. Returns (local, domain) or None. """
    if not email or '@' not in email:
        return None
    if email.count('@') != 1:
        return None
    email = email.strip().lower()
    local, domain = email.split('@', 1)
    if not local or not domain:
        return None
    try:
        domain = domain.encode('idna').decode('ascii')
    except UnicodeError:
        return None
    return local, domain


class EmailValidator(models.AbstractModel):
    _name = 'email.validator'
    _description = 'OdooSkills email hygiene validator (stateless)'

    @api.model
    def _check_role_based(self, local_part, domain):
        """ Check if local_part is a role-based address (admin@, sales@, etc.).
            Handles Gmail-style plus-tag aliases: info+newsletter → extracts base "info".
            Returns ('ok', None) or ('role_based', email).
        """
        normalized = (local_part or '').lower().strip()
        # base part before "+" suffix (Gmail-style alias separator)
        base = normalized.split('+', 1)[0]
        if normalized in ROLE_BASED_LOCAL_PARTS or base in ROLE_BASED_LOCAL_PARTS:
            return ('role_based', f"{local_part}@{domain}")
        return ('ok', None)

    @api.model
    def _check_syntax(self, email):
        """ Returns ('ok', None) or ('syntax_ko', email). """
        if not email:
            _logger.debug("email.validator syntax_ko: empty input")
            return ('syntax_ko', email)
        parts = _normalize_email(email)
        if parts is None:
            return ('syntax_ko', email)
        local, domain = parts
        # normalize handles IDNA/structure; regex validates char classes and TLD format
        if not _EMAIL_RE.match(f"{local}@{domain}"):
            return ('syntax_ko', email)
        tld = domain.rsplit('.', 1)[-1]
        if tld in INVALID_TLDS:
            return ('syntax_ko', email)
        return ('ok', None)
