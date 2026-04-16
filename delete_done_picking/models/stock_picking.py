# models/stock_picking.py
from odoo import models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_force_delete(self):
        self.ensure_one()

        picking_id = self.id

        # suppression (ton code)
        self.env['stock.valuation.layer'].sudo().search([
            ('stock_move_id', 'in', self.move_ids.ids)
        ]).unlink()

        for move in self.move_ids:
            move._do_unreserve()

        self.move_ids.write({'state': 'draft'})
        self.write({'state': 'draft'})

        self.move_line_ids.unlink()
        self.move_ids.unlink()

        self.unlink()

        # ✅ REDIRECTION PROPRE
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transfers',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'target': 'current',
        }