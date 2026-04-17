from odoo import models, api,fields
import logging

_logger = logging.getLogger(__name__)

# ----------------------------------------------------------
# Ajouter un champ pour marquer facture d’acompte fournisseur
# ----------------------------------------------------------
class AccountMove(models.Model):
    _inherit = 'account.move'

    is_supplier_downpayment = fields.Boolean(string="Facture d'acompte fournisseur")