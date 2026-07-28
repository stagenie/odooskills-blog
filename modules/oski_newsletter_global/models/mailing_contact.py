from odoo import api, models

GLOBAL_LIST_XMLID = 'mass_mailing.mailing_list_data'


class MailingContact(models.Model):
    _inherit = 'mailing.contact'

    @api.model
    def _oski_global_list(self):
        """La liste qui doit contenir tout le monde.

        Résolue par XML-ID plutôt que par nom : le libellé « Newsletter
        Globale » est éditable depuis l'interface et un renommage ne doit pas
        casser silencieusement la règle.
        """
        return self.env.ref(GLOBAL_LIST_XMLID, raise_if_not_found=False)

    def _oski_ensure_global_list(self):
        """Inscrit à la Globale ceux qui n'y sont pas encore.

        sudo : l'inscription peut venir du site public (snippet newsletter,
        popup) où l'utilisateur courant n'a aucun droit Marketing.
        L'appartenance à la Globale est une conséquence mécanique de
        l'inscription, pas un accès aux données.

        Un contact déjà présent est laissé tel quel, opt_out compris : une
        désinscription de la Globale ne doit pas être effacée par une
        inscription ultérieure à un segment.

        Le lien passe par l'écriture du Many2many `list_ids` et non par un
        `mailing.subscription.create` : la table de souscription porte le M2M,
        mais l'ORM n'invalide pas le cache de `list_ids` quand on écrit dans le
        modèle de relation directement — le contact semblait alors n'appartenir
        à aucune liste jusqu'au prochain vidage de cache.
        """
        lst = self._oski_global_list()
        if not lst:
            return
        known = self.env['mailing.subscription'].sudo().search([
            ('list_id', '=', lst.id),
            ('contact_id', 'in', self.ids),
        ]).contact_id
        todo = self.sudo() - known.sudo()
        if todo:
            todo.write({'list_ids': [(4, lst.id)]})

    @api.model_create_multi
    def create(self, vals_list):
        contacts = super().create(vals_list)
        contacts._oski_ensure_global_list()
        return contacts

    def write(self, vals):
        """Rattrape l'ajout d'un contact existant à un segment.

        Écrire `list_ids` n'appelle pas `mailing.subscription.create` : l'ORM
        insère directement dans la table de relation. Le hook sur la
        souscription ne voit donc passer que les créations explicites de
        souscriptions, et ce point d'entrée-ci couvre le reste.
        """
        res = super().write(vals)
        if 'list_ids' in vals or 'subscription_ids' in vals:
            self._oski_ensure_global_list()
        return res
