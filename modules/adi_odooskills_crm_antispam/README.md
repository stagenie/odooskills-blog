# adi_odooskills_crm_antispam

Anti-spam pour le pipeline CRM d'OdooSkills.

## Ce que fait le module

1. **Auto-archive à la création** — toute `crm.lead` dont `email_from` est dans `mail.blacklist` est créée avec `active=False` (n'apparaît jamais dans le pipeline).
2. **Action serveur "Marquer comme SPAM"** — bouton dans le menu ⚙️ Actions des vues list+form CRM. Sélectionne 1 ou N leads → blacklist l'email + archive le lead courant + archive tous les autres leads partageant le même `email_normalized`.

## Architecture

- **Models**
  - `crm.lead` (inherit) — override `create` (blacklist check) + nouvelle méthode `action_mark_as_spam()`
- **Data**
  - `data/server_actions.xml` — `ir.actions.server` avec `binding_model_id=crm.lead` et `binding_view_types='list,form'`

## Dépendances

- `crm`
- `mail` (pour `mail.blacklist`)
- `adi_odooskills_email_hygiene` (sibling — `email.validator` réutilisable pour purge manuelle ultérieure)

## Tests

```bash
cd /home/stadev/vscode-projects/odoo19-dev
./odoo/odoo-bin -c config/odoo.conf -d vs19_test_email_hygiene \
  -i adi_odooskills_crm_antispam --test-enable \
  --test-tags adi_odooskills_crm_antispam --stop-after-init
```

7 tests couvrent : create avec/sans blacklist, mark_as_spam mono+lot+sans email, archivage des leads soeurs, réactivation d'une entrée blacklist déjà archivée.

## Déploiement VPS prod (195.110.35.177, instance odoo19, port 8019)

```bash
# 1. Sync du module
rsync -avz --delete \
  /home/stadev/vscode-projects/odoo19-dev/addons/odooskills-blog/modules/adi_odooskills_crm_antispam/ \
  root@195.110.35.177:/opt/odoo19/odoo-custom-addons/adi_odooskills_crm_antispam/

# 2. (si pas déjà là) Sync de la dépendance email_hygiene
rsync -avz --delete \
  /home/stadev/vscode-projects/odoo19-dev/addons/odooskills-blog/modules/adi_odooskills_email_hygiene/ \
  root@195.110.35.177:/opt/odoo19/odoo-custom-addons/adi_odooskills_email_hygiene/

# 3. Install sur la base prod (DB = Odooskills)
ssh root@195.110.35.177 "systemctl stop odoo19 && \
  sudo -u odoo19 /opt/odoo19/odoo-venv/bin/python3 \
    /opt/odoo19/odoo/odoo-bin -c /etc/odoo19.conf \
    -d Odooskills -i adi_odooskills_crm_antispam --stop-after-init && \
  systemctl start odoo19"

# 4. Vérifier
ssh root@195.110.35.177 "journalctl -u odoo19 -n 30 --no-pager"
```

## Usage manuel — purge des leads spam existants

Dans CRM :
1. Pipeline > Vue Liste
2. Filtrer / sélectionner les leads spam (cocher checkbox de gauche)
3. Menu ⚙️ Actions > **Marquer comme SPAM**
4. Notification : "X lead(s) archivé(s) — Y email(s) ajouté(s) à la blacklist"

Tout futur lead avec ces emails sera automatiquement archivé à la création.

## Désarchiver un email blacklisté par erreur

Settings > Technical > Email > Blacklisted Email Addresses → désactiver l'entrée.

## Changelog

### 19.0.1.0.0 (2026-05-10)
- Initial release
- Override `crm.lead.create` avec check `mail.blacklist`
- Server action "Marquer comme SPAM" (binding list+form)
- 7 tests TransactionCase
