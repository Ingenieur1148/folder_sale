from odoo import api, models,fields, _

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    acompte_amount = fields.Monetary(
        string="Montant d'acompte",
        currency_field='currency_id',
        readonly=True
    )
    downpayment_amount = fields.Monetary(string="Montant acompte déjà payé")
    downpayment_invoice_id = fields.Many2one('account.move', string="Facture d'acompte")

    # is_account_forced_display = fields.Boolean(
    #     string="Afficher l'acompte",
    #     default=False
    # )
    downpayment_percent = fields.Float(
        string="Pourcentage d'acompte (%)",
        default=0.0,
        help="Pourcentage appliqué sur le montant total de la commande lors de la création d'un acompte."
    )
    def action_create_invoice(self):
        """Override to show a popup for advance vs regular invoice."""
        return {
            'name': _('Créer une facture'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.advance.payment.inv',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_purchase_id': self.id,
            }
        }

    downpayment_total = fields.Monetary(
        string="Total acomptes",
        currency_field='currency_id',
        readonly=False,
        default=0.0,
    )

    def _prepare_invoice(self):
        """
        Hérite de la préparation d'une facture depuis PO pour ajouter
        une ligne de déduction d'acompte si nécessaire.
        """
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()

        # Si des acomptes ont été payés / facturés pour ce PO, on les déduit
        if self.downpayment_total and self.currency_id and self.downpayment_total != 0.0:
            # Récupérer un compte comptable valable (ici on prend le compte payable fournisseur)
            account_id = False
            if self.partner_id.property_account_payable_id:
                account_id = self.partner_id.property_account_payable_id.id
            else:
                # fallback : premier compte payable trouvé
                account = self.env['account.account'].search([('user_type_id.type', '=', 'payable')], limit=1)
                account_id = account.id if account else False

            if not account_id:
                # si pas de compte, on lève une erreur pour forcer la configuration
                raise models.ValidationError(
                    _('Aucun compte fournisseur (payable) trouvé pour ajouter la ligne d\'acompte.'))

            # ajouter une ligne négative pour déduire les acomptes
            # on ajoute la ligne en fin (0,0,...)
            invoice_line = (0, 0, {
                'name': _('Déduction acompte') + ' - %s' % self.name,
                'quantity': 1.0,
                'price_unit': -abs(self.downpayment_total),
                'account_id': account_id,
            })
            # invoice_vals['invoice_line_ids'] doit être une liste de commandes, on ajoute la nôtre
            invoice_vals.setdefault('invoice_line_ids', [])
            invoice_vals['invoice_line_ids'].append(invoice_line)

        return invoice_vals