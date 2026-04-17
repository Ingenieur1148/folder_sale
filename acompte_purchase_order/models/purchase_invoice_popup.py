# -*- coding: utf-8 -*-
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PurchaseAdvancePaymentInv(models.TransientModel):
    _name = "purchase.advance.payment.inv"
    _description = "Facture fournisseur avec acompte"

    purchase_id = fields.Many2one(
        "purchase.order",
        string="Bon de commande",
        required=True
    )

    advance_payment_method = fields.Selection([
        ('regular', 'Facture normale'),
        ('advance_percent', 'Acompte (%)'),
        ('advance_fixed', 'Acompte (Montant fixe)'),
    ], string="Méthode d’acompte", default='regular')

    advance_percent = fields.Float(string="Pourcentage d'acompte (%)", default=0.0)
    advance_fixed = fields.Monetary(string="Montant fixe", currency_field='currency_id', default=0.0)
    advance_amount = fields.Monetary(string="Montant calculé", currency_field='currency_id', default=0.0)

    currency_id = fields.Many2one(
        'res.currency', related='purchase_id.currency_id', store=True, readonly=True
    )

    @api.onchange('advance_payment_method', 'advance_percent', 'advance_fixed', 'purchase_id')
    def _compute_advance_amount(self):
        """Calcul automatique du montant d'acompte pour affichage dans le wizard"""
        if not self.purchase_id:
            self.advance_amount = 0.0
            return

        if self.advance_payment_method == 'regular':
            self.advance_amount = 0.0
            self.advance_percent = 0.0
            self.advance_fixed = 0.0
        elif self.advance_payment_method == 'advance_percent':
            self.advance_amount = self.purchase_id.amount_total * (self.advance_percent / 100.0)
        else:  # advance_fixed
            self.advance_amount = self.advance_fixed

    def create_invoices(self):
        """Créer la facture fournisseur (normale ou acompte)"""
        self.ensure_one()
        purchase = self.purchase_id

        if not purchase:
            raise UserError(_("Veuillez sélectionner un bon de commande."))

        # ---------------------------
        # Compte fournisseur
        # ---------------------------
        account = purchase.partner_id.property_account_payable_id
        if not account:
            account = self.env['account.account'].search([
                ('user_type_id.type', '=', 'payable'),
                ('company_id','=', purchase.company_id.id)
            ], limit=1)
            if not account:
                raise UserError(_('Aucun compte fournisseur trouvé pour ce partenaire.'))

        # ---------------------------
        # Journal d'achat
        # ---------------------------
        journal = self.env['account.journal'].search([
            ('type', '=', 'purchase'),
            ('company_id','=', purchase.company_id.id)
        ], limit=1)
        if not journal:
            raise UserError(_('Veuillez créer un journal d\'achat pour cette société.'))

        # ---------------------------
        # Facture normale
        # ---------------------------
        if self.advance_payment_method == 'advance_percent':
            if self.advance_percent <= 0:
                raise UserError(_('Le pourcentage doit être supérieur à 0%.'))

            perc = self.advance_percent / 100
            label = _('Acompte %s%%') % self.advance_percent

            # Produit générique pour acompte
            deposit_product = self.env['product.product'].search([('name', '=', 'Acompte fournisseur')], limit=1)
            if not deposit_product:
                deposit_product = self.env['product.product'].create({
                    'name': 'Acompte fournisseur',
                    'type': 'service',
                    'standard_price': 0.0,
                    'list_price': 0.0,
                })

            # Création facture vide d’acompte
            invoice_vals = {
                'move_type': 'in_invoice',
                'partner_id': purchase.partner_id.id,
                'purchase_id': purchase.id,
                'invoice_origin': purchase.name,
                'currency_id': purchase.currency_id.id,
                'invoice_date': date.today(),
                'journal_id': journal.id,
                'company_id': purchase.company_id.id,
                'is_downpayment_invoice': True,
            }
            invoice = self.env['account.move'].create(invoice_vals)

            invoice_lines = []

            # 1 ligne d’acompte pour chaque produit
            for po_line in purchase.order_line:
                if not po_line.product_id:
                    continue

                subtotal = po_line.price_unit * po_line.product_qty
                advance_amount = subtotal * perc

                invoice_lines.append((0, 0, {
                    'product_id': deposit_product.id,
                    'name': f"{label} - {po_line.product_id.name}",
                    'quantity': 1,
                    'price_unit': advance_amount,
                    'tax_ids': [(6, 0, po_line.taxes_id.ids)],
                }))

            invoice.write({'invoice_line_ids': invoice_lines})

            # Calculer total et stocker sur la commande
            total_advance = sum(line[2]['price_unit'] for line in invoice_lines)
            purchase.write({
                'downpayment_amount': total_advance,
                'downpayment_invoice_id': invoice.id,
            })

            purchase.message_post(body=_("Facture d'acompte créée: %s") % invoice.name)
            return self._open_invoice(invoice)
        if self.advance_payment_method == 'regular':
            purchase = self.purchase_id

            # Vérifier si la commande a déjà un acompte enregistré
            total_advance = purchase.downpayment_amount
            if total_advance <= 0:
                raise UserError(_("Veuillez saisir un acompte valide (créez d'abord la facture d’acompte)."))

            invoice_lines = []

            # Produit "Acompte fournisseur"
            deposit_product = self.env['product.product'].search([('name', '=', 'Acompte fournisseur')], limit=1)
            if not deposit_product:
                deposit_product = self.env['product.product'].create({
                    'name': 'Acompte fournisseur',
                    'type': 'service',
                    'standard_price': 0.0,
                    'list_price': 0.0,
                    'invoice_policy': 'order',
                })

            # 🔹 Ajouter toutes les lignes produits originales
            for po_line in purchase.order_line:
                if not po_line.product_id:
                    continue
                account = po_line.product_id.property_account_expense_id \
                          or po_line.product_id.categ_id.property_account_expense_categ_id
                invoice_lines.append((0, 0, {
                    'product_id': po_line.product_id.id,
                    'name': po_line.name,
                    'quantity': po_line.product_qty,
                    'price_unit': po_line.price_unit,
                    'account_id': account.id if account else False,
                    'tax_ids': [(6, 0, po_line.taxes_id.ids)],
                }))

            # 🔹 Ajouter les lignes d’acompte proportionnelles
            total_po = sum(po_line.price_unit * po_line.product_qty for po_line in purchase.order_line)
            for po_line in purchase.order_line:
                if not po_line.product_id:
                    continue
                line_subtotal = po_line.price_unit * po_line.product_qty
                part = (line_subtotal / total_po) * total_advance
                account = po_line.product_id.property_account_expense_id \
                          or po_line.product_id.categ_id.property_account_expense_categ_id
                invoice_lines.append((0, 0, {
                    'product_id': deposit_product.id,
                    'name': f"Acompte - {po_line.product_id.name}",
                    'quantity': 1,
                    'price_unit': part,
                    'account_id': account.id if account else False,
                    'tax_ids': [(6, 0, po_line.taxes_id.ids)],
                }))

            # 🔹 Création de la facture normale
            invoice_vals = {
                'move_type': 'in_invoice',
                'partner_id': purchase.partner_id.id,
                'purchase_id': purchase.id,
                'invoice_origin': purchase.name,
                'currency_id': purchase.currency_id.id,
                'invoice_date': fields.Date.today(),
                'journal_id': journal.id,
                'company_id': purchase.company_id.id,
                'is_acompte_forced_display': True,
                'invoice_line_ids': invoice_lines,
            }

            invoice = self.env['account.move'].create(invoice_vals)

            # Message dans le chatter
            purchase.message_post(body=_("Facture normale créée avec acompte et produits: %s") % invoice.name)

            return self._open_invoice(invoice)




        else:  # advance_fixed
            if self.advance_fixed <= 0:
                raise UserError(_('Le montant de l\'acompte doit être supérieur à 0.'))
            amount = self.advance_fixed
            label = _('Acompte - %s') % purchase.name


    def _open_invoice(self, invoice):
        """Retourne l'action pour ouvrir la facture créée"""
        return {
            'name': _('Facture fournisseur'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
            'target': 'current',
        }
