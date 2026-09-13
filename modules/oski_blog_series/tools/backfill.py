"""Reprise des articles existants dans les séries (§9 de la spec).

Deux temps : `run(env, specs)` produit un aperçu sans rien écrire ;
`run(env, specs, apply=True)` écrit, et refuse si l'aperçu signale un problème."""
import re

from odoo.exceptions import UserError

MARKER = re.compile(r'Article\s*(\d+)\s*/\s*(\d+)')


def _block_uses_marker_order(block_items):
    """Vrai seulement si chaque article du bloc porte un marqueur « n/N » et que
    tous partagent le même total N (sinon les marqueurs, partiels ou incohérents,
    ne peuvent pas ordonner le bloc de façon fiable)."""
    if not block_items:
        return False
    totals = {item['marker_total'] for item in block_items}
    return None not in totals and len(totals) == 1


def build_plan(env, specs):
    # Les marqueurs « Article n/N » vivent dans le contenu français : lire en fr_FR
    # quand la langue est active, sinon garder celle de l'environnement appelant.
    lang = 'fr_FR' if env['res.lang'].search_count([('code', '=', 'fr_FR')]) else env.context.get('lang')
    Post = env['blog.post'].with_context(active_test=False, lang=lang)
    Version = env['oski.blog.odoo.version']
    Tag = env['blog.tag'].with_context(lang=lang)
    plan, problems, notes, seen = [], [], [], {}
    for spec in specs:
        version = Version.search([('code', '=', spec['version'])], limit=1) if spec['version'] else Version
        if spec['version'] and not version:
            problems.append("%s : version %s introuvable" % (spec['name'], spec['version']))
        tag = Tag.search([('name', '=', spec['tag'])], limit=1) if spec.get('tag') else Tag
        if spec.get('tag') and not tag:
            problems.append("%s : étiquette %s introuvable" % (spec['name'], spec['tag']))
        items = []
        for block_index, (block, ids) in enumerate(spec['blocks']):
            posts = Post.browse(ids).exists()
            missing = sorted(set(ids) - set(posts.ids))
            if missing:
                problems.append("%s : articles introuvables %s" % (spec['name'], missing))
            block_items = []
            # `posts` garde l'ordre de `ids` (celui de la table §9, l'ordre de
            # lecture) : c'est le repli utilisé quand les marqueurs ne suffisent pas.
            for mapping_index, post in enumerate(posts):
                if post.blog_id.id != spec['blog']:
                    problems.append("%s : l'article %s est dans le blog %s, attendu %s"
                                    % (spec['name'], post.id, post.blog_id.id, spec['blog']))
                if post.id in seen:
                    problems.append("l'article %s est dans deux séries : %s et %s"
                                    % (post.id, seen[post.id], spec['name']))
                seen[post.id] = spec['name']
                marker = MARKER.search(post.content or '')
                block_items.append({
                    'post': post, 'block': block, 'mapping_index': mapping_index,
                    'marker_n': int(marker.group(1)) if marker else None,
                    'marker_total': int(marker.group(2)) if marker else None,
                    'marker': '%s/%s' % marker.groups() if marker else False,
                })
            use_marker_order = _block_uses_marker_order(block_items)
            if not use_marker_order and any(item['marker'] for item in block_items):
                notes.append("%s : marqueurs partiels : ordre de la table (bloc %s)"
                             % (spec['name'], block or '(sans titre)'))
            for item in block_items:
                sort_value = item['marker_n'] if use_marker_order else item['mapping_index']
                items.append({
                    'key': (block_index, sort_value),
                    'post': item['post'], 'block': item['block'], 'marker': item['marker'],
                })
        items.sort(key=lambda item: item['key'])
        rows = [dict(item, position=position) for position, item in enumerate(items, start=1)]
        plan.append({'spec': spec, 'version': version, 'tag': tag, 'rows': rows})
    blog_ids = sorted({spec['blog'] for spec in specs})
    leftovers = Post.search([
        ('blog_id', 'in', blog_ids), ('is_published', '=', True), ('id', 'not in', list(seen)),
    ], order='blog_id, id')
    return plan, problems, leftovers, notes


def format_plan(plan, problems, leftovers, notes=()):
    lines = []
    for entry in plan:
        spec = entry['spec']
        lines.append("== %s | blog %s | %s | étiquette %s | %s" % (
            spec['name'], spec['blog'], entry['version'].name or 'Toutes versions',
            entry['tag'].name or '—', spec['audience']))
        for row in entry['rows']:
            lines.append("  %2d. [%s] %s%s%s" % (
                row['position'], row['post'].id, row['post'].name,
                " | bloc « %s »" % row['block'] if row['block'] else '',
                " | marqueur %s" % row['marker'] if row['marker'] else ''))
    lines.append("HORS SÉRIE (publiés, restent indépendants) : %d" % len(leftovers))
    lines.extend("  - [%s] blog %s | %s" % (post.id, post.blog_id.id, post.name) for post in leftovers)
    if notes:
        lines.append("INFORMATIONS : %d" % len(notes))
        lines.extend("  - %s" % note for note in notes)
    lines.append("PROBLÈMES : %d" % len(problems))
    lines.extend("  - %s" % problem for problem in problems)
    return '\n'.join(lines)


def apply_plan(env, plan):
    Series = env['oski.blog.series'].with_context(active_test=False)
    done = Series
    for sequence, entry in enumerate(plan, start=1):
        spec = entry['spec']
        vals = {
            'name': spec['name'],
            'blog_id': spec['blog'],
            'odoo_version_id': entry['version'].id or False,
            'tag_id': entry['tag'].id or False,
            'audience': spec['audience'],
            'description': spec['description'],
            'sequence': sequence * 10,
        }
        series = Series.search([('name', '=', spec['name']), ('blog_id', '=', spec['blog'])], limit=1)
        if series:
            series.write(vals)
        else:
            series = Series.create(vals)
        for row in entry['rows']:
            row['post'].write({
                'series_id': series.id,
                'series_position': row['position'],
                'series_block': row['block'] or False,
            })
        done |= series
    return done


def run(env, specs, apply=False):
    plan, problems, leftovers, notes = build_plan(env, specs)
    report = format_plan(plan, problems, leftovers, notes)
    if apply:
        if problems:
            raise UserError("Reprise refusée : %d problème(s) dans l'aperçu.\n%s"
                            % (len(problems), '\n'.join(problems)))
        apply_plan(env, plan)
    return report
