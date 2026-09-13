"""Aperçu HTML autonome du nettoyage des repères de série, avant toute écriture en production.

Usage (sans Odoo) :
    python3 markers_preview.py <prod_posts.json> <prod_series.json> <sortie.html>
"""
import collections
import html as html_lib
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import markers  # noqa: E402
import markers_curated  # noqa: E402

SITE = 'https://odooskills.com'
TRUNCATE = 400
CONTEXT = 160
RULES = {
    'R1': 'Bandeau numéroté',
    'R2': 'Navigation précédent / suivant',
    'R3': '« Voir aussi dans cette série »',
    'R4': 'Liste « La série »',
    'R5': 'Code T',
    'R6': 'Numérotation « x/y » en prose',
    'M': 'Remplacement manuel',
}
_LINK = re.compile(r'''href\s*=\s*["']((?:https?://[^/"']+)?/blog/([\w-]+)/([\w-]+)-(\d+))''')
_BLOG = re.compile(r'''href\s*=\s*["'](?:https?://[^/"']+)?/blog/([\w-]+-(\d+))[/"']''')


def _slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', text.replace("'", '')).strip('-')


def _urls(posts):
    """URL publique de chaque article, reprise des liens existants de l'instantané."""
    slugs, blogs = collections.defaultdict(set), {}
    for post in posts:
        for match in _LINK.finditer(post['content']):
            slugs[int(match.group(4))].add((match.group(2), match.group(3)))
        for match in _BLOG.finditer(post['content']):
            blogs.setdefault(int(match.group(2)), match.group(1))
    urls = {}
    for post in posts:
        name = _slugify(post['name'])
        found = slugs.get(post['id'])
        if found:
            blog, slug = max(found, key=lambda c: (c[1] == name, len(set(c[1].split('-')) & set(name.split('-')))))
        else:
            blog, slug = blogs.get(post['blog'], 'blog-%d' % post['blog']), name
        urls[post['id']] = '%s/blog/%s/%s-%d' % (SITE, blog, slug, post['id'])
    return urls


def _plain(fragment):
    """Texte visible d'un fragment ; une balise coupée en tête ou en queue de fenêtre est ignorée."""
    fragment = re.sub(r'^[^<]*>', '', fragment)
    fragment = re.sub(r'<[^>]*$', '', fragment)
    fragment = re.sub(r'^[#\w]{0,8};', '', fragment)      # entité coupée en tête (« bsp; »)
    fragment = re.sub(r'&[#\w]{0,8}$', '', fragment)      # entité coupée en queue (« &nbs »)
    return ' '.join(markers._lines(fragment))


def _cut(text, limit=TRUNCATE):
    return text if len(text) <= limit else text[:limit - 1] + '…'


def _hrefs(fragment):
    return set(re.findall(r'''href\s*=\s*["']([^"']+)''', fragment))


def _describe(current, edit):
    """Avant / après en texte brut, avec le texte voisin ; suppression : texte intégral."""
    index = current.find(edit.old)
    left = current[max(0, index - CONTEXT):index]
    right = current[index + len(edit.old):index + len(edit.old) + CONTEXT]
    item = {'rule': edit.rule, 'review': edit.review, 'links_added': sorted(_hrefs(edit.new) - _hrefs(edit.old)),
            'links_removed': sorted(_hrefs(edit.old) - _hrefs(edit.new))}
    if not edit.new:
        item['removed'] = _plain(edit.old)
    else:
        context = (_cut(_plain(left)), _cut(_plain(right)))
        item['before'] = (context[0], _plain(edit.old), context[1])
        item['after'] = (context[0], _plain(edit.new), context[1])
    return item


def build(posts, series):
    urls = _urls(posts)
    report, counts, dropped_total = [], collections.Counter(), 0
    for post in sorted(posts, key=lambda p: (p['blog'], p['series'] or 0, p['pos'] or 0, p['id'])):
        name = series[str(post['series'])]['name'] if post['series'] else False
        curated = markers_curated.CURATED.get(post['id'], ())
        drop = markers_curated.DROP.get(post['id'], ())
        plan = markers.build_post_plan(post['content'], name, bool(post['series']), curated, drop)
        proposals = markers.propose(post['content'], name, bool(post['series']))
        dropped = [e for e in proposals if any(x in e.old for x in drop)]
        dropped_total += len(dropped)
        manual_olds = {old for old, _new, _note in curated}
        notes = {old: note for old, _new, note in curated}
        items, current = [], post['content']
        for edit in plan:
            item = _describe(current, edit)
            item['manual'] = edit.old in manual_olds
            item['note'] = notes.get(edit.old, '')
            counts[(edit.rule, 'manuel' if item['manual'] else 'automatique')] += 1
            current, _statuses = markers.apply_edits(current, [edit])
            items.append(item)
        new_html, statuses = markers.apply_edits(post['content'], plan)
        failures = [(e.rule, s) for e, s in statuses if s != 'applied']
        residue = markers.residual_markers(new_html)
        accepted = markers_curated.ACCEPTED_RESIDUE.get(post['id'], [])
        report.append({
            'id': post['id'], 'name': post['name'], 'url': urls[post['id']], 'series': name,
            'items': items, 'dropped': [_plain(e.old) for e in dropped], 'failures': failures,
            'residue_unaccepted': [r for r in residue if r not in accepted],
            'residue_accepted': [r for r in residue if r in accepted],
        })
    return report, counts, dropped_total


CSS = """
:root { --ink:#1d232b; --muted:#5d6673; --line:#dfe3e8; --paper:#f7f8fa; --card:#fff;
        --del:#fde8e8; --del-ink:#8f1d1d; --add:#e5f5ea; --add-ink:#15612f; --accent:#6b3fa0; }
* { box-sizing: border-box; }
body { margin:0; padding:24px 16px 64px; background:var(--paper); color:var(--ink);
       font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif; }
main { max-width: 980px; margin: 0 auto; }
h1 { font-size: 1.6rem; margin: 0 0 .25rem; }
.lede { color: var(--muted); margin: 0 0 1.5rem; }
.summary { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin:0 0 1.25rem; }
.tile { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px 14px; }
.tile b { display:block; font-size:1.6rem; font-variant-numeric: tabular-nums; }
.tile span { color: var(--muted); font-size:.85rem; }
table.rules { width:100%; border-collapse:collapse; background:var(--card); border:1px solid var(--line);
              border-radius:10px; overflow:hidden; margin-bottom:2rem; }
.rules th, .rules td { text-align:left; padding:8px 12px; border-bottom:1px solid var(--line); }
.rules td.n { text-align:right; font-variant-numeric: tabular-nums; }
nav.toc { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px 16px; margin-bottom:2rem; }
nav.toc ol { columns: 2 320px; margin:.5rem 0 0; padding-left:1.2rem; }
nav.toc a { color: var(--accent); text-decoration:none; }
article { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px 18px; margin:0 0 18px; }
article h2 { font-size:1.1rem; margin:0; }
article h2 small { color:var(--muted); font-weight:normal; }
.meta { color:var(--muted); font-size:.85rem; margin:.2rem 0 .8rem; overflow-wrap:anywhere; }
.meta a { color: var(--accent); }
.change { border-top:1px solid var(--line); padding:10px 0 4px; }
.tag { display:inline-block; font-size:.75rem; font-weight:600; padding:1px 8px; border-radius:99px;
       background:#eef0f4; color:var(--ink); margin-right:6px; }
.tag.manual { background:#f1e8fb; color:var(--accent); }
.note { color:var(--muted); font-size:.85rem; }
.pair { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:6px; }
@media (max-width: 700px) { .pair { grid-template-columns:1fr; } }
.box { border-radius:8px; padding:8px 10px; font-size:.9rem; white-space:pre-wrap; overflow-wrap:anywhere; }
.box h4 { margin:0 0 4px; font-size:.75rem; text-transform:uppercase; letter-spacing:.04em; }
.before { background:var(--del); } .before h4 { color:var(--del-ink); }
.after { background:var(--add); } .after h4 { color:var(--add-ink); }
.box mark { background: rgba(0,0,0,.09); color: inherit; padding: 0 2px; border-radius: 3px; font-weight:600; }
.removed { background:var(--del); }
.links { font-size:.8rem; color:var(--muted); margin-top:4px; overflow-wrap:anywhere; }
.dropped { background:#fff8e6; border-radius:8px; padding:8px 10px; margin-top:10px; font-size:.85rem; }
.untouched { color: var(--muted); }
.final { background:var(--card); border:2px solid var(--line); border-radius:12px; padding:16px 18px; }
.ok { color: var(--add-ink); font-weight:600; }
.ko { color: var(--del-ink); font-weight:600; }
"""


def _esc(text):
    return html_lib.escape(text, quote=True)


def _pair(item):
    def box(kind, title, parts):
        left, middle, right = parts
        return ('<div class="box %s"><h4>%s</h4>%s<mark>%s</mark>%s</div>'
                % (kind, title, _esc(left + ' ' if left else ''), _esc(middle or '(rien)'), _esc(' ' + right if right else '')))
    return '<div class="pair">%s%s</div>' % (box('before', 'Avant', item['before']), box('after', 'Après', item['after']))


def render(report, counts, dropped_total):
    touched = [post for post in report if post['items']]
    total = sum(counts.values())
    manual = sum(n for (_rule, origin), n in counts.items() if origin == 'manuel')
    unaccepted = [post for post in report if post['residue_unaccepted'] or post['failures']]
    accepted = [post for post in report if post['residue_accepted']]
    out = ['<title>Nettoyage des repères de série</title>', '<style>%s</style>' % CSS, '<main>',
           '<h1>Nettoyage des repères de série — aperçu</h1>',
           '<p class="lead lede">Ce que deviendrait chaque article du blog OdooSkills : bandeaux numérotés, '
           'liens « précédent / suivant » écrits à la main, codes T01–T28 et numéros « article x/y ». '
           'Le module affiche désormais l\'étape de la série et sa navigation. Rien n\'est encore modifié en ligne.</p>',
           '<section class="summary">',
           '<div class="tile"><b>%d</b><span>modifications</span></div>' % total,
           '<div class="tile"><b>%d</b><span>dont relues et écrites à la main</span></div>' % manual,
           '<div class="tile"><b>%d</b><span>articles touchés sur %d</span></div>' % (len(touched), len(report)),
           '<div class="tile"><b>%d</b><span>propositions écartées à la relecture</span></div>' % dropped_total,
           '<div class="tile"><b>%d</b><span>résidus non acceptés</span></div>' % len(unaccepted),
           '</section>',
           '<table class="rules"><thead><tr><th>Règle</th><th class="n">Automatique</th><th class="n">Manuel</th></tr></thead><tbody>']
    for rule, label in RULES.items():
        auto, hand = counts.get((rule, 'automatique'), 0), counts.get((rule, 'manuel'), 0)
        if auto or hand:
            out.append('<tr><td>%s — %s</td><td class="n">%d</td><td class="n">%d</td></tr>' % (rule, _esc(label), auto, hand))
    out.append('</tbody></table>')
    out.append('<nav class="toc"><strong>Articles modifiés</strong><ol>')
    for post in touched:
        out.append('<li><a href="#a%d">%s</a> <small>(%d)</small></li>' % (post['id'], _esc(post['name']), len(post['items'])))
    out.append('</ol></nav>')
    for post in touched:
        out.append('<article id="a%d">' % post['id'])
        out.append('<h2>%s <small>· n° %d</small></h2>' % (_esc(post['name']), post['id']))
        out.append('<p class="meta"><a href="%s">%s</a>%s — %d modification(s)</p>' % (
            _esc(post['url']), _esc(post['url']),
            ' — série « %s »' % _esc(post['series']) if post['series'] else ' — hors série', len(post['items'])))
        for item in post['items']:
            tags = '<span class="tag">%s · %s</span>' % (item['rule'], _esc(RULES.get(item['rule'], item['rule'])))
            if item['manual']:
                tags += '<span class="tag manual">relu à la main</span>'
            out.append('<div class="change">%s' % tags)
            if item['note']:
                out.append('<span class="note">%s</span>' % _esc(item['note']))
            if 'removed' in item:
                out.append('<div class="box removed"><h4>Supprimé (texte intégral)</h4>%s</div>' % _esc(item['removed'] or '(bloc sans texte)'))
            else:
                out.append(_pair(item))
            links = []
            if item['links_removed']:
                links.append('lien retiré : ' + ', '.join(_esc(h) for h in item['links_removed']))
            if item['links_added']:
                links.append('lien ajouté : ' + ', '.join(_esc(h) for h in item['links_added']))
            if links:
                out.append('<div class="links">%s</div>' % ' · '.join(links))
            out.append('</div>')
        for text in post['dropped']:
            out.append('<div class="dropped"><strong>Proposition écartée, contenu gardé :</strong> %s</div>' % _esc(_cut(text)))
        out.append('</article>')
    untouched = [post for post in report if not post['items']]
    out.append('<p class="untouched">Articles sans modification : %s.</p>'
               % ', '.join('%s (n° %d)' % (_esc(p['name']), p['id']) for p in untouched))
    out.append('<section class="final"><h2>Résidus non acceptés</h2>')
    if unaccepted:
        out.append('<p class="ko">%d article(s) :</p><ul>' % len(unaccepted))
        for post in unaccepted:
            out.append('<li>n° %d : %s %s</li>' % (post['id'], _esc(' | '.join(post['residue_unaccepted'])), _esc(str(post['failures']))))
        out.append('</ul>')
    else:
        out.append('<p class="ok">Aucun : plus aucun repère de série détecté hors code, et toutes les modifications s\'appliquent.</p>')
    if accepted:
        out.append('<h3>Résidus acceptés</h3><ul>')
        for post in accepted:
            out.append('<li>n° %d : %s</li>' % (post['id'], _esc(' | '.join(post['residue_accepted']))))
        out.append('</ul>')
    out.append('</section></main>')
    return '\n'.join(out) + '\n'


def main(argv):
    if len(argv) != 4:
        sys.exit(__doc__)
    with open(argv[1], encoding='utf-8') as handle:
        posts = json.load(handle)
    with open(argv[2], encoding='utf-8') as handle:
        series = json.load(handle)
    report, counts, dropped_total = build(posts, series)
    with open(argv[3], 'w', encoding='utf-8') as handle:
        handle.write(render(report, counts, dropped_total))
    print('modifications=%d articles=%d écartées=%d résidus_non_acceptés=%d' % (
        sum(counts.values()), sum(1 for p in report if p['items']), dropped_total,
        sum(1 for p in report if p['residue_unaccepted'] or p['failures'])))


if __name__ == '__main__':
    main(sys.argv)
