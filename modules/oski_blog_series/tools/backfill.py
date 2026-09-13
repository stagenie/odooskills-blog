"""Reprise des articles existants dans les séries (§9 de la spec).

Deux temps : `run(env, specs)` produit un aperçu sans rien écrire ;
`run(env, specs, apply=True)` écrit, et refuse si l'aperçu signale un problème."""
import re

from odoo.exceptions import UserError

MARKER = re.compile(r'Article\s*(\d+)\s*/\s*(\d+)')
NO_MARKER = 10 ** 6


def build_plan(env, specs):
    # Les marqueurs « Article n/N » vivent dans le contenu français : lire en fr_FR
    # quand la langue est active, sinon garder celle de l'environnement appelant.
    lang = 'fr_FR' if env['res.lang'].search_count([('code', '=', 'fr_FR')]) else env.context.get('lang')
    Post = env['blog.post'].with_context(active_test=False, lang=lang)
    Version = env['oski.blog.odoo.version']
    Tag = env['blog.tag'].with_context(lang=lang)
    plan, problems, seen = [], [], {}
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
            for post in posts:
                if post.blog_id.id != spec['blog']:
                    problems.append("%s : l'article %s est dans le blog %s, attendu %s"
                                    % (spec['name'], post.id, post.blog_id.id, spec['blog']))
                if post.id in seen:
                    problems.append("l'article %s est dans deux séries : %s et %s"
                                    % (post.id, seen[post.id], spec['name']))
                seen[post.id] = spec['name']
                marker = MARKER.search(post.content or '')
                items.append({
                    'key': (block_index, int(marker.group(1)) if marker else NO_MARKER,
                            post.post_date, post.id),
                    'post': post, 'block': block,
                    'marker': '%s/%s' % marker.groups() if marker else False,
                })
        items.sort(key=lambda item: item['key'])
        rows = [dict(item, position=position) for position, item in enumerate(items, start=1)]
        plan.append({'spec': spec, 'version': version, 'tag': tag, 'rows': rows})
    blog_ids = sorted({spec['blog'] for spec in specs})
    leftovers = Post.search([
        ('blog_id', 'in', blog_ids), ('is_published', '=', True), ('id', 'not in', list(seen)),
    ], order='blog_id, id')
    return plan, problems, leftovers


def format_plan(plan, problems, leftovers):
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
    plan, problems, leftovers = build_plan(env, specs)
    report = format_plan(plan, problems, leftovers)
    if apply:
        if problems:
            raise UserError("Reprise refusée : %d problème(s) dans l'aperçu.\n%s"
                            % (len(problems), '\n'.join(problems)))
        apply_plan(env, plan)
    return report
