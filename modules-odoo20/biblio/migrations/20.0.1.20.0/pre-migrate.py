"""Avant le chargement de data/library.genre.csv : rattacher les genres déjà saisis à la main.

Sans ce script, un genre « Roman » créé dans l'interface fait échouer la mise à jour
(index unique sur le nom) : le fichier de données veut créer un second « Roman ».
Avec lui, la ligne du fichier trouve son identifiant externe et met à jour le genre existant.
"""
import csv

from odoo.tools.misc import file_open


def migrate(cr, version):
    with file_open('biblio/data/library.genre.csv') as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        cr.execute("""
            INSERT INTO ir_model_data (module, name, model, res_id, noupdate)
            SELECT 'biblio', %(xid)s, 'library.genre', g.id, false
              FROM library_genre g
             WHERE g.name->>'en_US' = %(name)s
               AND NOT EXISTS (
                   SELECT 1 FROM ir_model_data d WHERE d.module = 'biblio' AND d.name = %(xid)s
               )
        """, {'xid': row['id'], 'name': row['name']})
