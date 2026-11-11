from odoo import fields, models
from odoo.exceptions import UserError


class OskiCodeMixin(models.AbstractModel):
    """Un code lisible 'PRÉFIXE-00042', posé une seule fois, sur n'importe quel modèle."""
    _name = 'oski.code.mixin'
    _description = 'Code lisible (mixin)'
    _oski_code_prefixe = 'REF'

    oski_code = fields.Char('Code', copy=False, index=True, readonly=True)

    def action_oski_generer_code(self):
        for record in self:
            if record.oski_code:
                raise UserError(self.env._("%s a déjà un code.", record.display_name))
            record.oski_code = '%s-%05d' % (self._oski_code_prefixe, record.id)
        return True
