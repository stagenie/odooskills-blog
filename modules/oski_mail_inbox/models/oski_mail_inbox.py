from odoo import fields, models


class OskiMailInbox(models.Model):
    _name = 'oski.mail.inbox'
    _description = 'Email reçu'
    _inherit = ['mail.thread']
    _rec_name = 'subject'

    subject = fields.Char(string='Sujet')
