# Nettoyage des repères de série écrits à la main. À passer à `odoo-bin shell` sur la base cible :
#   aperçu      : OSKI_MARKERS_BLOG=<id> odoo-bin shell -c <conf> -d <base> --no-http < run_markers_shell.py
#   application : OSKI_MARKERS=apply OSKI_MARKERS_BLOG=<id> odoo-bin shell … < run_markers_shell.py
# Sans OSKI_MARKERS_BLOG : tous les blogs. Sauvegarde dans OSKI_MARKERS_BACKUP_DIR (défaut /tmp).
# La transaction n'est validée qu'en application, après le contrôle relu en base ; sinon annulée.
import os

from odoo.addons.oski_blog_series.tools import markers_apply

MODE = os.environ.get('OSKI_MARKERS', '')
if MODE not in ('', 'preview', 'apply'):
    raise SystemExit("OSKI_MARKERS doit valoir « apply » ou rester vide (aperçu), reçu %r" % MODE)
APPLY = MODE == 'apply'
BLOG = os.environ.get('OSKI_MARKERS_BLOG', '').strip()
if BLOG and not BLOG.isdigit():
    raise SystemExit("OSKI_MARKERS_BLOG doit être un identifiant de blog, reçu %r" % BLOG)
BACKUP_DIR = os.environ.get('OSKI_MARKERS_BACKUP_DIR', '/tmp')

try:
    result = markers_apply.run(env, apply=APPLY, blog_id=int(BLOG) if BLOG else None,  # noqa: F821 (env fourni par le shell)
                               backup_dir=BACKUP_DIR)
except BaseException:
    env.cr.rollback()  # noqa: F821
    print("RESULT ÉCHEC — transaction annulée, rien n'a été validé")
    raise
if APPLY and result['written']:
    env.cr.commit()  # noqa: F821
    print("RESULT appliqué — %d article(s) validé(s), sauvegarde %s" % (len(result['written']), result['backup']))
elif APPLY:
    env.cr.rollback()  # noqa: F821
    print("RESULT application — rien à écrire")
else:
    env.cr.rollback()  # noqa: F821
    print("RESULT aperçu — rien n'a été écrit")
