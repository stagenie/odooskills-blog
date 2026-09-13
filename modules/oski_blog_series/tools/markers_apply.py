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

Concurrence — ne PAS lancer l'application pendant qu'un article est ouvert dans l'éditeur du site :
un enregistrement de l'éditeur renvoie tout l'ancien HTML et réintroduirait les repères. Protection
réelle contre une écriture concurrente validée : `SELECT … FOR UPDATE` en REPEATABLE READ lève une
erreur de sérialisation (le lanceur annule tout) ; la comparaison au contenu planifié ne voit, elle,
que les changements faits dans la même transaction.
"""
import json
import os
import time
from collections import Counter

from odoo.exceptions import UserError
from odoo.tools import config

from . import markers, markers_curated

EXCERPT = 80
BACKUP_SUBDIR = 'oski_blog_markers'


def _series_lang(env):
    # Comme tools/backfill.py : le nom de série sert au bandeau, lu en fr_FR si la langue est active.
    return 'fr_FR' if env['res.lang'].search_count([('code', '=', 'fr_FR')]) else env.context.get('lang')


def _excerpt(text):
    text = ' '.join((text or '').split())
    return text if len(text) <= EXCERPT else text[:EXCERPT - 1] + '…'


def _unaccepted(post_id, html):
    accepted = markers_curated.ACCEPTED_RESIDUE.get(post_id, ())
    return [extract for extract in markers.residual_markers(html) if extract not in accepted]


def _curated_ok(edit, status):
    return (status == 'already' and edit.new) or (status == 'missing' and not edit.new)


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
        again, detail = _classify_cleaned(post_id, new_html, series_name, has_series)
        if again not in ('already', 'clean'):
            return 'problem', plan, new_html, (
                "plan non idempotent : un second passage trouverait encore à modifier (%s)" % detail)
        return 'change', plan, new_html, ''

    if automatic == 0 and all(_curated_ok(edit, status) for edit, status in statuses):
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
    """(statut, détail) d'un HTML supposé nettoyé, pour le contrôle d'idempotence (sans récursion)."""
    curated = markers_curated.CURATED.get(post_id, ())
    drop = markers_curated.DROP.get(post_id, ())
    plan = markers.build_post_plan(html, series_name, has_series, curated, drop)
    automatic = plan[:len(plan) - len(curated)]
    _new, statuses = markers.apply_edits(html, plan)
    leftovers = ['%s « %s »' % (edit.rule, _excerpt(edit.old)) for edit in automatic]
    leftovers += ['%s %s « %s »' % (edit.rule, status, _excerpt(edit.old))
                  for edit, status in statuses[len(automatic):] if not _curated_ok(edit, status)]
    residue = _unaccepted(post_id, html)
    if leftovers or residue:
        return 'problem', ' ; '.join(leftovers + ['résidu « %s »' % r for r in residue])
    return ('already' if plan else 'clean'), ''


def _check_blog_id(blog_id):
    if blog_id is not None and (isinstance(blog_id, bool) or not isinstance(blog_id, int) or blog_id <= 0):
        raise UserError("Identifiant de blog invalide : %r (entier positif attendu)." % (blog_id,))


def _scan(env, blog_id=None):
    """Lit les articles en SQL (jsonb brut) et classe chacun. Ordre : blog, id."""
    _check_blog_id(blog_id)
    env['blog.post'].flush_model(['content', 'blog_id', 'series_id', 'is_published', 'active'])
    query = "SELECT id, blog_id, series_id, is_published, active, content FROM blog_post"
    params = []
    if blog_id is not None:
        query += " WHERE blog_id = %s"
        params.append(blog_id)
    env.cr.execute(query + " ORDER BY blog_id, id", params)
    records = env.cr.fetchall()

    series_ids = sorted({record[2] for record in records if record[2]})
    Series = env['oski.blog.series'].with_context(active_test=False, lang=_series_lang(env))
    series_names = {series.id: series.name for series in Series.browse(series_ids)}

    rows = []
    for post_id, post_blog_id, series_id, published, active, content in records:
        row = {'id': post_id, 'blog_id': post_blog_id, 'published': published, 'active': active,
               'original': content, 'status': 'clean', 'edits': [], 'langs': {}, 'detail': '', 'residue': 0}
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
            posts=0, archived=0, to_change=0, edits=0, already=0, clean=0, problems=0, residue=0))
        counts['posts'] += 1
        counts['archived'] += 0 if row['active'] else 1
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


def _flags(row):
    return ('' if row['published'] else ' · BROUILLON') + ('' if row['active'] else ' · ARCHIVÉ')


def _report(rows, blogs, emit):
    for blog, counts in sorted(blogs.items()):
        emit("RESULT blog %s : articles %d (dont archivés %d) · à modifier %d · modifications %d · "
             "déjà nettoyés %d · sans objet %d · problèmes %d · résidus %d" % (
                 blog, counts['posts'], counts['archived'], counts['to_change'], counts['edits'],
                 counts['already'], counts['clean'], counts['problems'], counts['residue']))
    for row in rows:
        if row['status'] == 'change':
            rules = Counter(edit.rule for edit in row['edits'])
            emit("RESULT   [%s] blog %s · %d modification(s) : %s%s" % (
                row['id'], row['blog_id'], len(row['edits']),
                ' '.join('%s×%d' % item for item in sorted(rules.items())), _flags(row)))
    for row in rows:
        if row['status'] == 'problem':
            emit("RESULT PROBLÈME [%s] blog %s%s : %s" % (row['id'], row['blog_id'], _flags(row), row['detail']))


def default_backup_dir():
    return os.path.join(config['data_dir'], BACKUP_SUBDIR)


def _write_backup(backup_dir, originals):
    """Sauvegarde {id: contenu jsonb d'origine}, fichier 0600, synchronisée sur disque avant toute écriture."""
    path = os.path.join(backup_dir, 'blog-markers-%s.json' % time.strftime('%Y%m%d-%H%M%S'))
    payload = json.dumps({str(post_id): content for post_id, content in sorted(originals.items())},
                         ensure_ascii=False, indent=1).encode('utf-8')
    try:
        os.makedirs(backup_dir, mode=0o700, exist_ok=True)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(payload)
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


def _check_written(env, plan, ids, blog_id):
    """Contrôle relu en base après écriture : (erreurs, résidus non admis)."""
    env.cr.execute("SELECT id, content FROM blog_post WHERE id = ANY(%s)", [ids])
    stored = dict(env.cr.fetchall())
    errors = ["[%s] valeur relue différente de la valeur écrite" % post_id
              for post_id in ids if stored.get(post_id) != plan[post_id]['langs']]
    after = {row['id']: row for row in _scan(env, blog_id)}
    residue = 0
    for post_id in ids:
        for lang, value in (stored.get(post_id) or {}).items():
            extracts = _unaccepted(post_id, value)
            residue += len(extracts)
            if extracts:
                errors.append("[%s] %s : résidu non admis %s" % (post_id, lang, ' | '.join(extracts)))
        row = after.get(post_id)
        if not row or row['status'] not in ('already', 'clean'):
            errors.append("[%s] second passage : %s" % (post_id, row['detail'] if row else 'article introuvable'))
    return errors, residue


def run(env, apply=False, blog_id=None, backup_dir=None):
    """Aperçu (défaut) ou application. Imprime des lignes « RESULT … » et renvoie un dict :
    {'apply', 'blog_id', 'blogs': {blog: compteurs}, 'problems', 'written', 'backup', 'lines'}.
    Sauvegarde par défaut dans `<data_dir>/oski_blog_markers/`."""
    _check_blog_id(blog_id)
    backup_dir = backup_dir or default_backup_dir()
    lines = []

    def emit(line):
        lines.append(line)
        print(line)

    rows = _scan(env, blog_id)
    plan, problems = _plan_and_problems(rows)
    blogs = _summary(rows)
    emit("RESULT %s · périmètre : %s" % ('APPLICATION' if apply else 'APERÇU',
                                         'blog %s' % blog_id if blog_id is not None else 'tous les blogs'))
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
    # Verrou des lignes. Une écriture concurrente déjà validée fait lever ce SELECT (sérialisation) ;
    # la comparaison attrape un changement fait plus tôt dans la même transaction.
    env.cr.execute("SELECT id, content FROM blog_post WHERE id = ANY(%s) ORDER BY id FOR UPDATE", [ids])
    current = dict(env.cr.fetchall())
    moved = [post_id for post_id in ids if current.get(post_id) != plan[post_id]['original']]
    if moved:
        raise UserError("Nettoyage refusé : contenu modifié depuis l'aperçu pour %s. Rien n'a été écrit."
                        % moved)

    backup = _write_backup(backup_dir, {post_id: plan[post_id]['original'] for post_id in ids})
    result['backup'] = backup
    emit("RESULT sauvegarde : %s (%d article(s))" % (backup, len(ids)))

    # Point de sauvegarde : si le contrôle relu échoue, les UPDATE sont annulés ici même,
    # quel que soit l'appelant.
    try:
        with env.cr.savepoint(flush=False):
            for post_id in ids:
                env.cr.execute(
                    "UPDATE blog_post SET content = %s::jsonb, write_date = (now() AT TIME ZONE 'UTC'), "
                    "write_uid = %s WHERE id = %s",
                    (json.dumps(plan[post_id]['langs']), env.uid, post_id))
                if env.cr.rowcount != 1:
                    raise UserError("Nettoyage interrompu : article %s non mis à jour." % post_id)
            env['blog.post'].invalidate_model(['content', 'write_date', 'write_uid'])
            errors, residue = _check_written(env, plan, ids, blog_id)
            emit("RESULT contrôle relu en base : %d article(s) · résidus non admis %d · erreurs %d"
                 % (len(ids), residue, len(errors)))
            if errors:
                raise UserError("Contrôle après écriture en échec, écritures annulées :\n%s" % '\n'.join(errors))
    except Exception:
        env['blog.post'].invalidate_model(['content', 'write_date', 'write_uid'])
        raise
    result['written'] = ids
    return result
