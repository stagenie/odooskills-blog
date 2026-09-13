# À passer à `odoo-bin shell` sur la base cible :
#   aperçu      : odoo-bin shell -c <conf> -d <base> --no-http < run_backfill_shell.py
#   application : OSKI_BACKFILL=apply odoo-bin shell … < run_backfill_shell.py
import os

from odoo.addons.oski_blog_series.tools import backfill, backfill_mapping

APPLY = os.environ.get('OSKI_BACKFILL') == 'apply'
print(backfill.run(env, backfill_mapping.SERIES, apply=APPLY))  # noqa: F821 (env fourni par le shell)
if APPLY:
    env.cr.commit()  # noqa: F821
    print("RESULT appliqué")
else:
    print("RESULT aperçu — rien n'a été écrit")
