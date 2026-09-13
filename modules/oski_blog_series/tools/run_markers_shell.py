# Nettoyage des repères de série écrits à la main. À passer à `odoo-bin shell` sur la base cible,
# les variables d'environnement APRÈS le changement d'utilisateur (sudo/su les effacent sinon) :
#   aperçu      : sudo -u odoo19 env OSKI_MARKERS=preview [OSKI_MARKERS_BLOG=<id>] <python> <odoo-bin> shell -c <conf> -d <base> --no-http < run_markers_shell.py
#   application : sudo -u odoo19 env OSKI_MARKERS=apply OSKI_MARKERS_BLOG=<id> <python> <odoo-bin> shell … < run_markers_shell.py
# OSKI_MARKERS : vide/preview = aperçu, apply = application ; toute autre valeur est refusée.
# OSKI_MARKERS_BLOG : entier positif (sans : tous les blogs). OSKI_MARKERS_BACKUP_DIR : défaut <data_dir>/oski_blog_markers.
# La première ligne RESULT donne le mode : si elle ne dit pas APPLICATION alors qu'on applique, STOP.
# La transaction n'est validée qu'en application, après le contrôle relu en base ; sinon annulée.
import os

from odoo.addons.oski_blog_series.tools import markers_apply


def parse(environ):
    """(apply, blog_id, backup_dir) ; SystemExit sur toute valeur invalide, avant tout accès à la base."""
    mode = environ.get('OSKI_MARKERS', '')
    if mode not in ('', 'preview', 'apply'):
        raise SystemExit("OSKI_MARKERS doit valoir « apply », « preview » ou rester vide, reçu %r" % mode)
    blog = environ.get('OSKI_MARKERS_BLOG', '').strip()
    blog_id = None
    if blog:
        if not blog.isdigit() or int(blog) <= 0:
            raise SystemExit("OSKI_MARKERS_BLOG doit être un entier positif, reçu %r" % blog)
        blog_id = int(blog)
    return mode == 'apply', blog_id, environ.get('OSKI_MARKERS_BACKUP_DIR') or None


def main(env, environ=None):
    apply, blog_id, backup_dir = parse(os.environ if environ is None else environ)
    print("RESULT %s · blog %s · sauvegarde %s" % (
        'APPLICATION' if apply else 'APERÇU', blog_id if blog_id is not None else 'tous',
        backup_dir or markers_apply.default_backup_dir()))
    try:
        result = markers_apply.run(env, apply=apply, blog_id=blog_id, backup_dir=backup_dir)
    except BaseException:
        env.cr.rollback()
        print("RESULT ÉCHEC — transaction annulée, rien n'a été validé")
        raise
    if apply and result['written']:
        env.cr.commit()
        print("RESULT appliqué — %d article(s) validé(s), sauvegarde %s" % (len(result['written']), result['backup']))
    elif apply:
        env.cr.rollback()
        print("RESULT application — rien à écrire")
    else:
        env.cr.rollback()
        print("RESULT aperçu — rien n'a été écrit")
    return result


if __name__ == '__main__':
    main(env)  # noqa: F821 (env fourni par odoo-bin shell)
