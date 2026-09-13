"""Application du nettoyage des repères de série dans la base (tâche 4).

`run(env)` montre ce qui serait écrit ; `run(env, apply=True)` écrit, dans la transaction
courante, et refuse tout article à problème (rien n'est écrit). L'appelant valide la
transaction (voir `run_markers_shell.py`).

Classement de chaque article (le HTML est lu tel quel dans le jsonb, toutes langues) :
- `change` : chaque modification du plan est `applied`, le résultat n'a plus de résidu non
  admis et un second passage sur ce résultat ne trouverait plus rien (sinon : problème) ;
- `already` : déjà nettoyé — aucune proposition automatique, chaque entrée CURATED est
  `already` (remplacement) ou `missing` (suppression), résidus admis ; rien n'est écrit ;
- `clean` : aucun plan et aucun résidu non admis ;
- `problem` : tout le reste (langues divergentes, `old` absent ou ambigu, état partiel,
  résidu non admis, plan non idempotent).
"""
import json
import os
import time
from collections import Counter

from odoo.exceptions import UserError

from . import markers, markers_curated

EXCERPT = 80


def _series_lang(env):
    # Comme tools/backfill.py : le nom de série sert au bandeau, lu en fr_FR si la langue est active.
    return 'fr_FR' if env['res.lang'].search_count([('code', '=', 'fr_FR')]) else env.context.get('lang')


def _excerpt(text):
    text = ' '.join((text or '').split())
    return text if len(text) <= EXCERPT else text[:EXCERPT - 1] + '…'


def _unaccepted(post_id, html):
    accepted = markers_curated.ACCEPTED_RESIDUE.get(post_id, ())
    return [extract for extract in markers.residual_markers(html) if extract not in accepted]


def _classify(post_id, html, series_name, has_series):
    """(statut, plan, nouveau HTML, détail du problème)."""
    curated = markers_curated.CURATED.get(post_id, ())
    drop = markers_curated.DROP.get(post_id, ())
    plan = markers.build_post_plan(html, series_name, has_series, curated, drop)
    automatic = len(plan) - len(curated)
    new_html, statuses = markers.apply_edits(html, plan)

    if plan and all(status == 'applied' for _edit, status in statuses):
        residue = _unaccepted(post_id, new_html)
        if residue:
            return 'problem', plan, new_html, "résidu non admis après nettoyage : %s" % ' | '.join(residue)
        again, _plan, _html, _detail = _classify_cleaned(post_id, new_html, series_name, has_series)
        if again not in ('already', 'clean'):
            return 'problem', plan, new_html, (
                "plan non idempotent : un second passage trouverait encore à modifier (%s)" % _detail)
        return 'change', plan, new_html, ''

    already = automatic == 0 and all(
        (status == 'already' and edit.new) or (status == 'missing' and not edit.new)
        for edit, status in statuses)
    if already:
        residue = _unaccepted(post_id, html)
        if residue:
            return 'problem', plan, html, "résidu non admis : %s" % ' | '.join(residue)
        return ('already' if plan else 'clean'), plan, html, ''

    failures = ['%s %s « %s »' % (edit.rule, status, _excerpt(edit.old))
                for edit, status in statuses if status != 'applied']
    detail = ("état partiel ou modification introuvable : %s" % ' ; '.join(failures)
              if failures else "état partiel : %d proposition(s) automatique(s) encore applicable(s) "
                               "alors que des remplacements manuels sont déjà faits" % automatic)
    return 'problem', plan, html, detail


def _classify_cleaned(post_id, html, series_name, has_series):
    """Classement d'un HTML supposé nettoyé, pour le contrôle d'idempotence (sans récursion)."""
    curated = markers_curated.CURATED.get(post_id, ())
    drop = markers_curated.DROP.get(post_id, ())
    plan = markers.build_post_plan(html, series_name, has_series, curated, drop)
    automatic = plan[:len(plan) - len(curated)]
    _new, statuses = markers.apply_edits(html, plan)
    leftovers = ['%s « %s »' % (edit.rule, _excerpt(edit.old)) for edit in automatic]
    leftovers += ['%s %s « %s »' % (edit.rule, status, _excerpt(edit.old))
                  for edit, status in statuses[len(automatic):]
                  if not ((status == 'already' and edit.new) or (status == 'missing' and not edit.new))]
    residue = _unaccepted(post_id, html)
    if leftovers or residue:
        return 'problem', plan, html, ' ; '.join(leftovers + ['résidu « %s »' % r for r in residue])
    return ('already' if plan else 'clean'), plan, html, ''


def _scan(env, blog_id=None):
    """Lit les articles en SQL (jsonb brut) et classe chacun. Ordre : blog, id."""
    env['blog.post'].flush_model(['content', 'blog_id', 'series_id', 'is_published'])
    query = "SELECT id, blog_id, series_id, is_published, content FROM blog_post"
    params = []
    if blog_id:
        query += " WHERE blog_id = %s"
        params.append(blog_id)
    env.cr.execute(query + " ORDER BY blog_id, id", params)
    records = env.cr.fetchall()

    series_ids = sorted({series_id for _id, _blog, series_id, _pub, _content in records if series_id})
    Series = env['oski.blog.series'].with_context(active_test=False, lang=_series_lang(env))
    series_names = {series.id: series.name for series in Series.browse(series_ids)}

    rows = []
    for post_id, post_blog_id, series_id, published, content in records:
        row = {'id': post_id, 'blog_id': post_blog_id, 'published': published, 'original': content,
               'status': 'clean', 'edits': [], 'langs': {}, 'detail': '', 'residue': 0}
        rows.append(row)
        if content is None:
            continue
        if not isinstance(content, dict) or not all(isinstance(value, str) for value in content.values()):
            row.update(status='problem', detail="contenu jsonb inattendu (%s)" % type(content).__name__)
            continue
        if not content:
            continue
        values = set(content.values())
        if len(values) > 1:
            row.update(status='problem', detail="contenu différent selon la langue (%s) : refus"
                                                % ', '.join(sorted(content)))
            continue
        html = values.pop()
        status, plan, new_html, detail = _classify(
            post_id, html, series_names.get(series_id, False), bool(series_id))
        row.update(status=status, detail=detail, residue=len(_unaccepted(post_id, new_html)))
        if status == 'change':
            row.update(edits=plan, langs={lang: new_html for lang in content})
        elif status in ('already', 'problem'):
            row['edits'] = plan
    return rows


def _plan_and_problems(rows):
    plan = {row['id']: {'edits': row['edits'], 'langs': row['langs'], 'blog_id': row['blog_id'],
                        'original': row['original'], 'published': row['published']}
            for row in rows if row['status'] == 'change'}
    problems = ["[%s] %s" % (row['id'], row['detail']) for row in rows if row['status'] == 'problem']
    return plan, problems


def build_plan(env, blog_id=None):
    """({post_id: {'edits': [Edit], 'langs': {lang: nouveau HTML}, …}}, problèmes).
    Le plan ne contient que les articles à écrire ; rien n'est écrit."""
    return _plan_and_problems(_scan(env, blog_id))


def _summary(rows):
    blogs = {}
    for row in rows:
        counts = blogs.setdefault(row['blog_id'], Counter(
            posts=0, to_change=0, edits=0, already=0, clean=0, problems=0, residue=0))
        counts['posts'] += 1
        counts['residue'] += row['residue']
        if row['status'] == 'change':
            counts['to_change'] += 1
            counts['edits'] += len(row['edits'])
        elif row['status'] == 'already':
            counts['already'] += 1
        elif row['status'] == 'clean':
            counts['clean'] += 1
        else:
            counts['problems'] += 1
    return {blog: dict(counts) for blog, counts in blogs.items()}


def _report(rows, blogs, emit):
    for blog, counts in sorted(blogs.items()):
        emit("RESULT blog %s : articles %d · à modifier %d · modifications %d · déjà nettoyés %d · "
             "sans objet %d · problèmes %d · résidus %d" % (
                 blog, counts['posts'], counts['to_change'], counts['edits'], counts['already'],
                 counts['clean'], counts['problems'], counts['residue']))
    for row in rows:
        if row['status'] == 'change':
            rules = Counter(edit.rule for edit in row['edits'])
            emit("RESULT   [%s] blog %s · %d modification(s) : %s%s" % (
                row['id'], row['blog_id'], len(row['edits']),
                ' '.join('%s×%d' % item for item in sorted(rules.items())),
                '' if row['published'] else ' · BROUILLON'))
    for row in rows:
        if row['status'] == 'problem':
            emit("RESULT PROBLÈME [%s] blog %s : %s" % (row['id'], row['blog_id'], row['detail']))


def _write_backup(backup_dir, originals):
    """Sauvegarde {id: contenu jsonb d'origine}, synchronisée sur disque avant toute écriture."""
    path = os.path.join(backup_dir, 'blog-markers-%s.json' % time.strftime('%Y%m%d-%H%M%S'))
    try:
        with open(path, 'x', encoding='utf-8') as handle:
            json.dump({str(post_id): content for post_id, content in sorted(originals.items())},
                      handle, ensure_ascii=False, indent=1)
            handle.flush()
            os.fsync(handle.fileno())
        directory = os.open(backup_dir, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError as error:
        raise UserError("Nettoyage refusé : sauvegarde impossible dans %s (%s). Rien n'a été écrit."
                        % (backup_dir, error)) from error
    return path


def run(env, apply=False, blog_id=None, backup_dir='/tmp'):
    """Aperçu (défaut) ou application. Imprime des lignes « RESULT … » et renvoie un dict :
    {'apply', 'blog_id', 'blogs': {blog: compteurs}, 'problems', 'written', 'backup'}."""
    lines = []

    def emit(line):
        lines.append(line)
        print(line)

    rows = _scan(env, blog_id)
    plan, problems = _plan_and_problems(rows)
    blogs = _summary(rows)
    emit("RESULT %s · périmètre : %s" % ('APPLICATION' if apply else 'APERÇU',
                                         'blog %s' % blog_id if blog_id else 'tous les blogs'))
    _report(rows, blogs, emit)
    result = {'apply': apply, 'blog_id': blog_id, 'blogs': blogs, 'problems': problems,
              'written': [], 'backup': None, 'lines': lines}

    if not apply:
        emit("RESULT aperçu — rien n'a été écrit")
        return result
    if problems:
        raise UserError("Nettoyage refusé : %d problème(s), rien n'a été écrit.\n%s"
                        % (len(problems), '\n'.join(problems)))
    if not plan:
        emit("RESULT rien à écrire")
        return result

    ids = sorted(plan)
    # Verrouille les lignes et vérifie qu'elles n'ont pas bougé depuis la lecture du plan.
    env.cr.execute("SELECT id, content FROM blog_post WHERE id = ANY(%s) ORDER BY id FOR UPDATE", [ids])
    current = dict(env.cr.fetchall())
    moved = [post_id for post_id in ids if current.get(post_id) != plan[post_id]['original']]
    if moved:
        raise UserError("Nettoyage refusé : contenu modifié depuis l'aperçu pour %s. Rien n'a été écrit."
                        % moved)

    backup = _write_backup(backup_dir, {post_id: plan[post_id]['original'] for post_id in ids})
    result['backup'] = backup
    emit("RESULT sauvegarde : %s (%d article(s))" % (backup, len(ids)))

    for post_id in ids:
        env.cr.execute("UPDATE blog_post SET content = %s::jsonb, write_date = now() WHERE id = %s",
                       (json.dumps(plan[post_id]['langs']), post_id))
        if env.cr.rowcount != 1:
            raise UserError("Nettoyage interrompu : article %s non mis à jour (transaction à annuler)." % post_id)
    env['blog.post'].invalidate_model(['content', 'write_date'])
    result['written'] = ids

    # Contrôle final, relu en base : valeurs écrites, résidus, second passage sans effet.
    env.cr.execute("SELECT id, content FROM blog_post WHERE id = ANY(%s)", [ids])
    stored = dict(env.cr.fetchall())
    errors = ["[%s] valeur relue différente de la valeur écrite" % post_id
              for post_id in ids if stored.get(post_id) != plan[post_id]['langs']]
    after = {row['id']: row for row in _scan(env, blog_id)}
    residue = 0
    for post_id in ids:
        for lang, value in stored.get(post_id, {}).items():
            extracts = _unaccepted(post_id, value)
            residue += len(extracts)
            if extracts:
                errors.append("[%s] %s : résidu non admis %s" % (post_id, lang, ' | '.join(extracts)))
        row = after.get(post_id)
        if not row or row['status'] not in ('already', 'clean'):
            errors.append("[%s] second passage : %s" % (post_id, row['detail'] if row else 'article introuvable'))
    emit("RESULT contrôle relu en base : %d article(s) · résidus non admis %d · erreurs %d"
         % (len(ids), residue, len(errors)))
    if errors:
        raise UserError("Contrôle après écriture en échec, la transaction doit être annulée :\n%s"
                        % '\n'.join(errors))
    return result
