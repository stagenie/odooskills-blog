"""Repères de série écrits à la main dans les articles : règles pures (sans Odoo).

Chaque règle propose des `Edit` exacts : `old` est une sous-chaîne du HTML d'origine
(jamais re-sérialisé), `new` son remplacement. `review=True` signale un cas à relire.
Le contenu de <pre>, <code>, <script>, <style> et des commentaires n'est jamais modifié.

Utilisable sans Odoo : `sys.path.insert(0, <tools>); import markers`."""
import html as html_lib
import re
from collections import namedtuple

Edit = namedtuple('Edit', 'rule old new review')

# ---------------------------------------------------------------------------
# Lecture du HTML (positions dans la chaîne d'origine)
# ---------------------------------------------------------------------------

_TOKEN = re.compile(
    r'<!--.*?-->'
    r'|<(script|style)\b(?:[^>"\']|"[^"]*"|\'[^\']*\')*>.*?</\1\s*>'
    r'|<(/?)([a-zA-Z][\w:-]*)((?:[^>"\']|"[^"]*"|\'[^\']*\')*)>',
    re.S | re.I)
_VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta',
         'param', 'source', 'track', 'wbr'}
_BLOCK = {'address', 'article', 'aside', 'blockquote', 'br', 'dd', 'div', 'dl', 'dt', 'figcaption',
          'figure', 'footer', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'hr', 'li', 'nav', 'ol',
          'p', 'pre', 'section', 'table', 'td', 'th', 'tr', 'ul'}
_HEADINGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}


class _El:
    __slots__ = ('tag', 'start', 'open_end', 'close_start', 'end', 'parent', 'attrs')

    def __init__(self, tag, start, open_end, parent, attrs):
        self.tag, self.start, self.open_end, self.parent, self.attrs = tag, start, open_end, parent, attrs
        self.close_start = self.end = None

    def contains(self, other):
        return self.start <= other.start and other.end <= self.end and self is not other


def _elements(html):
    """Éléments fermés du document, dans l'ordre d'ouverture (tolérant : une fermeture
    sans ouverture est ignorée, un élément non fermé est abandonné)."""
    elements, stack = [], []
    for match in _TOKEN.finditer(html):
        tag = match.group(3)
        if tag is None:
            continue  # commentaire ou script/style : contenu opaque
        tag = tag.lower()
        if not match.group(2):
            attrs = match.group(4)
            if tag in _VOID or attrs.rstrip().endswith('/'):
                continue
            element = _El(tag, match.start(), match.end(), stack[-1] if stack else None, attrs)
            elements.append(element)
            stack.append(element)
            continue
        for depth in range(len(stack) - 1, -1, -1):
            if stack[depth].tag == tag:
                stack[depth].close_start, stack[depth].end = match.start(), match.end()
                del stack[depth:]
                break
    return [element for element in elements if element.end is not None]


def _inner(html, element):
    return html[element.open_end:element.close_start]


def _text(fragment):
    """Texte visible d'un fragment, espaces normalisés."""
    fragment = re.sub(r'<!--.*?-->', ' ', fragment, flags=re.S)
    return re.sub(r'\s+', ' ', html_lib.unescape(re.sub(r'<[^>]*>', ' ', fragment))).strip()


def _lines(fragment):
    """Texte visible découpé aux frontières de blocs (les balises en ligne sont fusionnées)."""
    fragment = re.sub(r'<!--.*?-->', '', fragment, flags=re.S)

    def tag(match):
        name = match.group(1).lower()
        return '\n' if name in _BLOCK else ''
    fragment = re.sub(r'</?([a-zA-Z][\w:-]*)(?:[^>"\']|"[^"]*"|\'[^\']*\')*>', tag, fragment)
    lines = [re.sub(r'\s+', ' ', html_lib.unescape(line)).strip() for line in fragment.split('\n')]
    return [line for line in lines if line]


def protected_spans(html):
    """Zones jamais modifiées : <pre>, <code>, <script>, <style>, commentaires. Triées, fusionnées."""
    spans = [(m.start(), m.end()) for m in _TOKEN.finditer(html) if m.group(3) is None]
    spans += [(e.start, e.end) for e in _elements(html) if e.tag in ('pre', 'code')]
    merged = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _in_protected(spans, start, end):
    """Vrai si [start, end) touche une zone protégée sans la contenir entièrement."""
    for p_start, p_end in spans:
        if p_start < end and start < p_end and not (start <= p_start and p_end <= end):
            return True
    return False


def _contains_block_code(html, start, end):
    return re.search(r'<(pre|script|style)\b', html[start:end], re.I) is not None


# ---------------------------------------------------------------------------
# R1 — bandeau numéroté
# ---------------------------------------------------------------------------

_EYEBROW_CLASS = re.compile(r'''\bclass\s*=\s*["'][^"']*\b(text-warning|text-uppercase)\b''')
_EYEBROW_TRIGGER = re.compile(
    r'Article\s*\d+\s*/\s*\d+|Bloc \d|Saison[^·<]*·\s*Article|Série[^·<]*·\s*Article'
    r'|·\s*\d+\s*/\s*\d+|Fin d[eu] (?:la )?(?:Saison|Bloc) \d')
_EYEBROW_SEPARATOR = re.compile(r'\s+(?:·|&middot;|—|&mdash;)\s+')
_EYEBROW_DROP = re.compile(
    r'(?:Bloc \d+|Saison\b.*|Série\b.*|(?:Article\s*)?\d+\s*/\s*\d+(?:\s*\(.*\))?'
    r'|Fin d[eu] (?:la )?(?:Bloc|Saison|série)\b.*|closing|final|fin|série complète)', re.I | re.S)
# Bandeau sans la classe attendue (Saisons 11 et 12 : `class="lead mb-2"`) : tout le paragraphe
# doit avoir la forme d'un bandeau. Proposé à relire.
_LOOSE_EYEBROW = re.compile(r'(?:Saison|Série|Bloc)\b.{0,100}?(?:Article\s*\d+\s*/\s*\d+|·\s*\d+\s*/\s*\d+)')
_LOOSE_EYEBROW_MAX = 120


def _eyebrow_candidates(html, series_name):
    spans = protected_spans(html)
    candidates = []
    for element in _elements(html):
        if element.tag != 'p':
            continue
        inner = _inner(html, element)
        classed = _EYEBROW_CLASS.search(element.attrs) is not None
        if classed:
            if not _EYEBROW_TRIGGER.search(html_lib.unescape(inner)) and not _EYEBROW_TRIGGER.search(inner):
                continue
        else:
            text = _text(inner)
            if '<' in inner or len(text) > _LOOSE_EYEBROW_MAX or not _LOOSE_EYEBROW.match(text):
                continue
        if _in_protected(spans, element.start, element.end):
            continue
        segments = [s.strip() for s in _EYEBROW_SEPARATOR.split(inner.strip())]
        kept = [s for s in segments if s and not _EYEBROW_DROP.fullmatch(s)]
        review = not classed or '<' in inner or len(kept) > 1
        if kept:
            theme = ' — '.join(kept)
        elif series_name:
            theme = html_lib.escape(series_name, quote=False)
        else:
            continue  # ni thème ni série : rien de sûr à proposer
        new = html[element.start:element.open_end] + theme + html[element.close_start:element.end]
        candidates.append((element.start, element.end, Edit('R1', html[element.start:element.end], new, review)))
    return candidates


def eyebrow_edits(html, series_name):
    return _finalize(html, _eyebrow_candidates(html, series_name))


# ---------------------------------------------------------------------------
# R2 — navigation précédent / suivant
# ---------------------------------------------------------------------------

_ARROW = re.compile(r'[←→⟵⟶]')
_PREV_NEXT_WORD = re.compile(r'pr[ée]c[ée]dent|suivant', re.I)
_CAPTIONS = (
    re.compile(r'^Suite de la Saison\b'),
    re.compile(r'^Série\b.*\bArticle\s*\d+\s*/\s*\d+'),
    re.compile(r'^Série\s*«[^»]*»\s*·\s*\d+\s*/\s*\d+'),
)
_NEXT_HEADING = re.compile(r'^(?:prochain(?:e)?\s+(?:article|étape|épisode)|article suivant)\b', re.I)
NAV_MAX_RESIDUE = 40
NAV_MAX_SECTION_TEXT = 400


def _is_nav_link(html, link):
    label = _text(_inner(html, link))
    return bool(label) and (label.startswith(('←', '⟵')) or label.endswith(('→', '⟶'))
                            or _PREV_NEXT_WORD.search(label) is not None)


def _nav_residue(html, start, end, links):
    """Texte restant une fois retirés les textes de liens, les flèches et les légendes de série."""
    parts, cursor = [], start
    for link in sorted(links, key=lambda l: l.start):
        if link.start >= cursor and link.end <= end:
            parts.append(html[cursor:link.start])
            cursor = link.end
    parts.append(html[cursor:end])
    lines = _lines('\n'.join(parts))
    lines = [line for line in lines if not any(caption.search(line) for caption in _CAPTIONS)]
    return re.sub(r'\s+', ' ', _ARROW.sub(' ', ' '.join(lines))).strip()


_HREF = re.compile(r'''\bhref\s*=\s*["']([^"']*)''', re.I)
_BLOG_URL = re.compile(r'(?:https?://[^/]+)?/blog/')


def _links_leave_blog(links):
    hrefs = [m.group(1) for m in (_HREF.search(link.attrs) for link in links) if m]
    return any(not _BLOG_URL.match(href) for href in hrefs)


def _has_nav_signal(html, start, end):
    """Un vrai repère précédent/suivant (pas une simple flèche de bouton « Découvrir → »)."""
    fragment_text = ' '.join(_lines(html[start:end]))
    if re.search(r'[←⟵]', fragment_text) or _PREV_NEXT_WORD.search(fragment_text):
        return True
    return any(caption.search(line) for line in _lines(html[start:end]) for caption in _CAPTIONS)


def _nav_candidates(html):
    elements = _elements(html)
    spans = protected_spans(html)
    candidates = []
    sections = [e for e in elements if e.tag == 'section']
    for section in sections:
        if any(section.contains(other) for other in sections):
            continue  # seulement les sections sans section imbriquée
        if _in_protected(spans, section.start, section.end):
            continue
        inside = [e for e in elements if section.contains(e)]
        links = [e for e in inside if e.tag == 'a']
        nav_links = [link for link in links if _is_nav_link(html, link)]
        if not nav_links:
            continue
        if len(_text(_inner(html, section))) > NAV_MAX_SECTION_TEXT:
            continue
        headings = [e for e in inside if e.tag in ('h2', 'h3')]
        if any(_NEXT_HEADING.match(_text(_inner(html, h))) for h in headings):
            continue  # bloc « Prochain article » avec résumé : on garde
        start, end = section.open_end, section.close_start
        if (len(_nav_residue(html, start, end, links)) < NAV_MAX_RESIDUE
                and _has_nav_signal(html, start, end)):
            # Un lien hors du blog (ex. « Récupérer le guide technique ») partirait avec la section.
            review = _contains_block_code(html, section.start, section.end) or _links_leave_blog(links)
            candidates.append((section.start, section.end, Edit('R2', html[section.start:section.end], '', review)))
            continue
        # Section mixte : le plus petit bloc qui contient tous les liens de navigation…
        blocks = [e for e in inside if e.tag in ('div', 'p') and all(e.contains(l) for l in nav_links)]
        if not blocks:
            continue
        block = min(blocks, key=lambda e: e.end - e.start)
        block_links = [l for l in links if block.contains(l)]
        if (len(_nav_residue(html, block.open_end, block.close_start, block_links)) >= NAV_MAX_RESIDUE
                or not _has_nav_signal(html, block.open_end, block.close_start)
                or any(block.contains(h) for h in headings)):
            continue
        # …remonté à travers les enveloppes qui ne contiennent rien d'autre.
        while block.parent is not None and block.parent is not section and block.parent.tag in ('div', 'p'):
            parent = block.parent
            outside = html[parent.open_end:block.start] + html[block.end:parent.close_start]
            if outside.strip():
                break
            block = parent
        candidates.append((block.start, block.end, Edit('R2', html[block.start:block.end], '', True)))
    return candidates


def nav_edits(html):
    return _finalize(html, _nav_candidates(html))


# ---------------------------------------------------------------------------
# R3 — « Voir aussi dans cette série » ; R4 — « La série — … »
# ---------------------------------------------------------------------------

_SEE_ALSO = re.compile(r'Voir aussi dans cette s[ée]rie', re.I)
_SERIES_TITLE = re.compile(r'^La s[ée]rie\b')


def _innermost_sections(html, elements):
    sections = [e for e in elements if e.tag == 'section']
    return [s for s in sections if not any(s.contains(other) for other in sections)]


def _see_also_candidates(html):
    elements = _elements(html)
    spans = protected_spans(html)
    candidates = []
    for section in _innermost_sections(html, elements):
        headings = [e for e in elements if section.contains(e) and e.tag in _HEADINGS]
        if not any(_SEE_ALSO.search(_text(_inner(html, h))) for h in headings):
            continue
        if _in_protected(spans, section.start, section.end):
            continue
        review = _contains_block_code(html, section.start, section.end)
        candidates.append((section.start, section.end, Edit('R3', html[section.start:section.end], '', review)))
    return candidates


def see_also_series_edits(html):
    return _finalize(html, _see_also_candidates(html))


def _series_list_candidates(html):
    elements = _elements(html)
    spans = protected_spans(html)
    candidates = []
    for section in _innermost_sections(html, elements):
        inside = [e for e in elements if section.contains(e)]
        headings = [e for e in inside if e.tag in ('h2', 'h3', 'h4')]
        titles = [h for h in headings if _SERIES_TITLE.match(_text(_inner(html, h)))]
        if not titles or _in_protected(spans, section.start, section.end):
            continue
        title = titles[0]
        following = [e for e in inside if e.start >= title.end and e.parent is title.parent]
        if (not following or following[0].tag not in ('ul', 'ol', 'div')
                or html[title.end:following[0].start].strip()):
            continue
        listing = following[0]
        # Une grille de cartes (`div`, articles 137 et 171) peut mêler des liens hors série : à relire.
        grid = listing.tag == 'div'
        remainder = html[section.open_end:title.start] + html[listing.end:section.close_start]
        if not _text(remainder) and not re.search(r'<a\b', remainder, re.I):
            # La section ne contient que le titre et sa liste : elle part entière.
            review = grid or _contains_block_code(html, section.start, section.end)
            candidates.append((section.start, section.end, Edit('R4', html[section.start:section.end], '', review)))
            continue
        # Autre contenu dans la section (phrase, navigation, bloc « Côté fonctionnel ») :
        # seulement le titre et la liste qui le suit, à relire.
        candidates.append((title.start, listing.end, Edit('R4', html[title.start:listing.end], '', True)))
    return candidates


def series_list_edits(html):
    return _finalize(html, _series_list_candidates(html))


# ---------------------------------------------------------------------------
# R5 — codes T dans les libellés (liens et titres)
# ---------------------------------------------------------------------------

_T_PREFIX = re.compile(r'^(\s*(?:←|&larr;)?\s*)T[0-2]\d\b\s*(?:—|&mdash;|-|:)\s*')
_T_SUFFIX = re.compile(r'\s*(?:—|&mdash;|-)\s*T[0-2]\d\b(?:\s*·[^<]*?)?(\s*(?:→|&rarr;)?\s*)$')
_T_ALONE = re.compile(r'^\s*T[0-2]\d\s*$')


def _tcode_candidates(html):
    spans = protected_spans(html)
    candidates = []
    for element in _elements(html):
        is_heading = element.tag in _HEADINGS
        if element.tag != 'a' and not is_heading:
            continue
        if _in_protected(spans, element.start, element.end) or any(
                p_start <= element.start < p_end for p_start, p_end in spans):
            continue
        inner = _inner(html, element)
        if is_heading and re.search(r'<a\b', inner, re.I):
            continue  # le lien intérieur est traité pour lui-même
        old = html[element.start:element.end]
        if element.tag == 'a' and _T_ALONE.match(inner):
            candidates.append((element.start, element.end, Edit('R5', old, old, True)))
            continue
        new_inner = _T_PREFIX.sub(r'\1', inner, count=1)
        new_inner = _T_SUFFIX.sub(r'\1', new_inner, count=1)
        if new_inner == inner:
            continue
        new = html[element.start:element.open_end] + new_inner + html[element.close_start:element.end]
        candidates.append((element.start, element.end, Edit('R5', old, new, False)))
    return candidates


def tcode_label_edits(html):
    return _finalize(html, _tcode_candidates(html))


# ---------------------------------------------------------------------------
# Résidus, application, proposition
# ---------------------------------------------------------------------------

_RESIDUAL = re.compile(
    r'\bT[0-2]\d\b|(?i:article \d+ ?/ ?\d+)|Bloc \d+ ·|Voir aussi dans cette s[ée]rie'
    r'|<h[2-4][^>]*>\s*La s[ée]rie|Suite de la Saison')
RESIDUAL_EXCERPT = 120


def residual_markers(html):
    """Extraits (≤ 120 c.) autour de chaque marqueur R1–R6 hors zones protégées."""
    masked = list(html)
    for start, end in protected_spans(html):
        masked[start:end] = ' ' * (end - start)
    masked = ''.join(masked)
    found = []
    for match in _RESIDUAL.finditer(masked):
        window = masked[max(0, match.start() - 40):match.end() + 60]
        found.append(re.sub(r'\s+', ' ', window).strip()[:RESIDUAL_EXCERPT])
    return found


def apply_edits(html, edits):
    """Applique les Edit dans l'ordre. Statuts :
    - applied : `old` présent une fois ;
    - ambiguous : `old` présent plusieurs fois ;
    - already : `old` absent, `new` non vide et présent ;
    - missing : sinon. Une suppression (`new == ''`) dont `old` est absent est donc toujours
      `missing`, jamais `already` : on ne distingue pas « déjà retiré » de « jamais existé ».
      L'idempotence au niveau de l'article est du ressort de l'appelant.
    Si un statut est missing ou ambiguous, rien n'est appliqué (HTML d'origine renvoyé)."""
    result, statuses = html, []
    for edit in edits:
        count = result.count(edit.old)
        if count == 1:
            result = result.replace(edit.old, edit.new, 1)
            statuses.append((edit, 'applied'))
        elif count > 1:
            statuses.append((edit, 'ambiguous'))
        elif edit.new and edit.new in result:
            statuses.append((edit, 'already'))
        else:
            statuses.append((edit, 'missing'))
    if any(status in ('missing', 'ambiguous') for _edit, status in statuses):
        return html, statuses
    return result, statuses


def _dedupe(candidates):
    """Retire les propositions contenues dans une autre (ou qui la chevauchent) : la plus large gagne."""
    ordered = sorted(candidates, key=lambda c: (c[0], -(c[1] - c[0])))
    kept = []
    for start, end, edit in ordered:
        if kept and start < kept[-1][1]:
            continue  # contenue dans la précédente, ou la chevauche
        kept.append((start, end, edit))
    return kept


def _widen(html, start, end, low, high, step=16):
    """Plus court élargissement (à gauche, à droite ou des deux côtés, dans [low, high])
    qui rend html[start:end] unique ; (start, end) si aucun n'y parvient."""
    best = None
    for grow_left, grow_right in ((1, 0), (0, 1), (1, 1)):
        left, right = start, end
        while html.count(html[left:right]) > 1:
            wider = (max(low, left - step * grow_left), min(high, right + step * grow_right))
            if wider == (left, right):
                break
            left, right = wider
        if html.count(html[left:right]) == 1 and (best is None or right - left < best[1] - best[0]):
            best = (left, right)
    return best or (start, end)


def _finalize(html, candidates):
    """Sans chevauchement, dans l'ordre du document ; `old` rendu unique en l'élargissant
    de texte voisin inchangé, sans jamais empiéter sur une autre proposition."""
    kept = _dedupe(candidates)
    spans = protected_spans(html)
    edits = []
    for index, (start, end, edit) in enumerate(kept):
        low = kept[index - 1][1] if index else 0
        high = kept[index + 1][0] if index + 1 < len(kept) else len(html)
        # L'élargissement ne franchit jamais une zone protégée (<pre>, <code>, commentaire…).
        low = max([low] + [p_end for _p_start, p_end in spans if p_end <= start])
        high = min([high] + [p_start for p_start, _p_end in spans if p_start >= end])
        left, right = start, end
        if html.count(html[start:end]) > 1:
            left, right = _widen(html, start, end, low, high)
            if html.count(html[left:right]) > 1:
                # Unicité impossible sans franchir une limite : `old` étroit, à relire
                # (apply_edits le signalera « ambiguous »).
                edit = edit._replace(review=True)
        if (left, right) != (start, end):
            prefix, suffix = html[left:start], html[end:right]
            edit = edit._replace(old=prefix + edit.old + suffix, new=prefix + edit.new + suffix)
        edits.append(edit)
    return edits


def propose(html, series_name, has_series):
    """R1 + (R2 si l'article a une série) + R3 + R4 + R5, dédoublonnés et sans chevauchement."""
    candidates = _eyebrow_candidates(html, series_name)
    if has_series:
        candidates += _nav_candidates(html)
    candidates += _see_also_candidates(html) + _series_list_candidates(html) + _tcode_candidates(html)
    return _finalize(html, candidates)
