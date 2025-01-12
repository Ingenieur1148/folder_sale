from odoo import api, fields, models, _, Command

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'
    status_folder_id = fields.Many2one('status.folder', string="Status Folder")