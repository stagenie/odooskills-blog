import logging
import os
import re
import time

import dns.resolver
from dns.exception import DNSException, Timeout
from dns.resolver import NXDOMAIN, NoAnswer

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

DNS_TIMEOUT_SEC = 3.0
MX_CACHE_TTL_SEC = 3600
MX_CACHE_TTL_TIMEOUT_SEC = 60  # transient: short TTL so legitimate users can retry
MX_CACHE_MAXSIZE = 1024

# Module-level cache: {domain: (status, expiry_monotonic)}
_MX_CACHE = {}

ROLE_BASED_LOCAL_PARTS = frozenset({
    'admin', 'administrator', 'contact', 'hello', 'help', 'hr', 'info',
    'jobs', 'mail', 'marketing', 'no-reply', 'noreply', 'office',
    'postmaster', 'sales', 'support',
})


def _load_disposable_set():
    """ Load disposable_domains.txt once at import time → frozenset. """
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, '..', 'data', 'disposable_domains.txt')
    domains = set()
    try:
        with open(path, encoding='utf-8') as f:
            for line in f:
                line = line.strip().lower()
                if line and not line.startswith('#'):
                    domains.add(line)
    except FileNotFoundError:
        _logger.warning("Disposable list not found at %s — disposable check disabled", path)
    except Exception as e:
        _logger.warning(
            "Failed to load disposable list at %s: %s — disposable check disabled",
            path, e,
        )
    return frozenset(domains)


DISPOSABLE_SET = _load_disposable_set()


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
    def _check_disposable(self, domain):
        """ Check if domain is a known disposable email service.
            Returns ('ok', None) or ('disposable', domain).
        """
        if (domain or '').lower().strip() in DISPOSABLE_SET:
            return ('disposable', domain)
        return ('ok', None)

    @api.model
    def _resolve_mx(self, domain):
        """ Resolve MX record for a domain.
            Returns ('ok', None), ('mx_ko', domain), or ('dns_timeout', domain).
            In-memory TTL cache (1h, max 1024 entries) avoids hammering DNS
            on repeated submissions. NXDOMAIN/NoAnswer are also cached.
        """
        domain = (domain or '').lower().strip()
        if not domain:
            return ('mx_ko', domain)
        now = time.monotonic()
        cached = _MX_CACHE.get(domain)
        if cached is not None:
            status, expiry = cached
            if now < expiry:
                if status == 'ok':
                    return ('ok', None)
                return (status, domain)
            _MX_CACHE.pop(domain, None)
        # cache miss → resolve
        try:
            answers = dns.resolver.resolve(domain, 'MX', lifetime=DNS_TIMEOUT_SEC)
            status = 'ok' if any(a for a in answers) else 'mx_ko'
        except (NXDOMAIN, NoAnswer):
            status = 'mx_ko'
        except (Timeout, DNSException):
            status = 'dns_timeout'
        # Eviction: if full, drop one arbitrary entry (insertion-ordered dict)
        if len(_MX_CACHE) >= MX_CACHE_MAXSIZE:
            _MX_CACHE.pop(next(iter(_MX_CACHE)), None)
        ttl = MX_CACHE_TTL_TIMEOUT_SEC if status == 'dns_timeout' else MX_CACHE_TTL_SEC
        _MX_CACHE[domain] = (status, now + ttl)
        if status == 'ok':
            return ('ok', None)
        return (status, domain)

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

    @api.model
    def validate(self, email):
        """ Top-level: returns ('valid', None) or (reason_code, email).
            reason_code in {syntax_ko, role_based, disposable, mx_ko, dns_timeout}.
            On any rejection, the SECOND tuple element is the ORIGINAL email
            string (preserves case/whitespace for logging and UI display).
            Short-circuits: syntax → role-based → disposable → MX (cheapest first).
        """
        # 1. Syntax (also normalizes & idna-encodes)
        status, _reason = self._check_syntax(email)
        if status != 'ok':
            return ('syntax_ko', email)
        # _check_syntax only returns 'ok' if _normalize_email succeeded → guaranteed non-None
        local, domain = _normalize_email(email)

        # 2. Role-based local-part
        status, _reason = self._check_role_based(local, domain)
        if status != 'ok':
            return ('role_based', email)

        # 3. Disposable domain
        status, _reason = self._check_disposable(domain)
        if status != 'ok':
            return ('disposable', email)

        # 4. DNS MX
        status, _reason = self._resolve_mx(domain)
        if status != 'ok':
            return (status, email)  # 'mx_ko' or 'dns_timeout'

        return ('valid', None)
