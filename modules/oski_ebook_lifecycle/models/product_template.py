from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ebook_ids = fields.Many2many(
        'oski.ebook', 'oski_ebook_product_rel', 'product_tmpl_id', 'ebook_id',
        string='Ebooks inclus',
        help="Ebooks accordés à l'achat de ce produit (mono ou pack).")
    lifecycle_tier_category_id = fields.Many2one(
        'res.partner.category', string='Tier client',
        help="Tag tier posé à l'achat (ex. Client Pack, Client Trilogie). Vide sur un mono-ebook.")
    oski_price_regular = fields.Float(
        string='Prix régulier (€)', digits='Product Price',
        help="Prix de référence EUR affiché barré. Source de vérité du barré.")
    oski_price_launch = fields.Float(
        string='Prix remisé (€)', digits='Product Price',
        help="Prix EUR effectivement payé. Égal au régulier si pas de remise.")
    oski_launch_deadline = fields.Datetime(
        string='Fin de la remise',
        help="Vide = remise sans date (barré permanent, pas de compte à rebours). "
             "Rempli = lancement daté avec compte à rebours + retour auto au régulier.")
    oski_pack_bonus = fields.Float(
        string='Bonus pack (€)', digits='Product Price',
        help="Remise bundle retranchée à la somme des membres (assistant prix pack).")

    def _oski_apply_pricing_offer(self):
        """Estampille les emplacements natifs depuis les champs d'offre.
        list_price = launch*rate ; compare_list_price = regular*rate (0 si pas de remise).
        Item pricelist EUR = launch (daté si deadline, + item régulier de repli)."""
        ICP = self.env['ir.config_parameter'].sudo()
        rate = float(ICP.get_param('oski.pricing.dzd_rate') or 270.0)
        pl_id = int(ICP.get_param('oski.pricing.eur_pricelist_id') or 0)
        pricelist = self.env['product.pricelist'].browse(pl_id).exists()
        Item = self.env['product.pricelist.item']
        for rec in self.filtered(lambda p: p.ebook_ids):
            reg = rec.oski_price_regular
            launch = rec.oski_price_launch or reg
            rec.list_price = round(launch * rate, 2)
            rec.compare_list_price = round(reg * rate, 2) if reg > launch else 0.0
            if not pricelist:
                continue
            Item.search([('pricelist_id', '=', pricelist.id),
                         ('product_tmpl_id', '=', rec.id)]).unlink()
            base = {'pricelist_id': pricelist.id, 'product_tmpl_id': rec.id,
                    'applied_on': '1_product', 'compute_price': 'fixed'}
            if rec.oski_launch_deadline:
                Item.create({**base, 'fixed_price': launch,
                             'date_end': rec.oski_launch_deadline})
                Item.create({**base, 'fixed_price': reg,
                             'date_start': rec.oski_launch_deadline})
            else:
                Item.create({**base, 'fixed_price': launch})

    def oski_pricing_incoherences(self):
        """Retourne la liste des divergences entre champs d'offre et emplacements natifs."""
        ICP = self.env['ir.config_parameter'].sudo()
        rate = float(ICP.get_param('oski.pricing.dzd_rate') or 270.0)
        pl_id = int(ICP.get_param('oski.pricing.eur_pricelist_id') or 0)
        Item = self.env['product.pricelist.item']
        issues = []
        for rec in self.filtered(lambda p: p.ebook_ids):
            tag = rec.default_code or rec.display_name
            reg, launch = rec.oski_price_regular, (rec.oski_price_launch or rec.oski_price_regular)
            exp_compare = round(reg * rate, 2) if reg > launch else 0.0
            if abs(rec.compare_list_price - exp_compare) > 0.01:
                issues.append('%s: barré %.2f attendu %.2f' % (tag, rec.compare_list_price, exp_compare))
            if abs(rec.list_price - round(launch * rate, 2)) > 0.01:
                issues.append('%s: list_price %.2f attendu %.2f' % (tag, rec.list_price, launch * rate))
            if pl_id:
                now = fields.Datetime.now()
                active = Item.search([
                    ('pricelist_id', '=', pl_id), ('product_tmpl_id', '=', rec.id),
                    '|', ('date_start', '=', False), ('date_start', '<=', now),
                    '|', ('date_end', '=', False), ('date_end', '>', now)])
                if len(active) > 1:
                    # Plusieurs items actifs simultanément = ambiguïté sur le prix
                    # réellement appliqué par Odoo. Ne jamais masquer via min().
                    issues.append('%s: %d items pricelist actifs simultanément' % (tag, len(active)))
                elif not active or abs(active.fixed_price - launch) > 0.01:
                    issues.append('%s: item pricelist actif ≠ %.2f' % (tag, launch))
        return issues
