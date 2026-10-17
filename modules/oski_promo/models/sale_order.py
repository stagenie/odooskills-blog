from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_reward_values_discount(self, reward, coupon, **kwargs):
        """Remise standard, puis mise à l'échelle pour atteindre le prix net garanti.

        Odoo calcule la remise en pourcentage du prix de ligne du moment. Avec
        un prix net garanti, la remise voulue est « prix de ligne − prix net »,
        que le prix de liste soit le tarif courant ou un prix de lancement. On
        garde la ventilation par taxe produite par le standard et on multiplie
        chaque ligne de remise par le même facteur.
        """
        values = super()._get_reward_values_discount(reward, coupon, **kwargs)
        net_price = reward.oski_net_price
        if not net_price or reward.discount_applicability != 'specific':
            return values
        lines = self._get_specific_discountable_lines(reward).filtered(
            lambda line: line.product_uom_qty and line.price_total)
        if not lines:
            return values
        discountable = sum(lines.mapped('price_total'))
        quantity = sum(lines.mapped('product_uom_qty'))
        unit_net = reward.currency_id._convert(
            net_price, self.currency_id, self.company_id, fields.Date.today())
        wanted = max(0.0, discountable - unit_net * quantity)
        wanted = min(wanted, self.amount_total)
        current = -sum(v['price_unit'] * v.get('product_uom_qty', 1.0) for v in values)
        if self.currency_id.is_zero(current) or self.currency_id.is_zero(current - wanted):
            return values
        factor = wanted / current
        for v in values:
            v['price_unit'] = self.currency_id.round(v['price_unit'] * factor)
        return values
