from odoo import api, fields, models, _, Command

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'
    folder_id = fields.Many2one('status.folder')
    folder_state = fields.Selection(
        string='Folder State',
        related="folder_id.state",
        store=True,
        readonly=False,
    )

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            folder = self.env['status.folder'].search([('partner_id', '=', self.partner_id.id)], limit=1)
            self.folder_state = folder.state if folder else False
        else:
            self.folder_state = False

class StatusFolder(models.Model):
    _name = 'status.folder'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'analytic.mixin']
    product_id=fields.Many2one('product.product',string="Services")
    document_attach = fields.Many2many('ir.attachment', 'document', string="Attachment")
    document_instruire = fields.Many2many('ir.attachment', 'document', string="Attachment")
    document_encour = fields.Many2many('ir.attachment', 'document', string="Attachment")
    document_autorisations = fields.Many2many('ir.attachment', 'document', string="Attachment")
    document_octroyees = fields.Many2many('ir.attachment', 'document', string="Attachment")
    document_planifiee = fields.Many2many('ir.attachment', 'document', string="Attachment")
    document_effectuee = fields.Many2many('ir.attachment', 'document', string="Attachment")
    document_subvention_en_cours = fields.Many2many('ir.attachment', 'document', string="Attachment")
    document_subvention_finalisee = fields.Many2many('ir.attachment', 'document', string="Attachment")
    name = fields.Char(string="Name Folder",required=True)
    partner_id= fields.Many2one('res.partner',required=True)
    sale_id = fields.Many2one('sale.order', compute='_compute_sale_id', store=True)
    sale_order_ids = fields.One2many('sale.order', 'folder_id', string="Sale Orders")

    state = fields.Selection([
        ('attente', 'En attente de document'),
        ('reception_a_compte', 'Reception 1er acompte'),
        ('instruire', 'A instruire'),
        ('encours', 'En cours instruction'),
        ('autorisations', 'Autorisations finalisées'),
        ('octroyees', 'Autorisations octroyées'),
        ('planifiee', 'Pose planifiée'),
        ('effectuee', 'Pose effectuée'),
        ('subvention en cours', 'Subvention en cours'),
        ('subvention finalisee', 'Subvention finalisée')
    ], 'Status', default='attente', index=True, required=True)

    @api.depends('partner_id')
    def _compute_sale_id(self):
        for record in self:
            # Find the sale order associated with the selected partner
            sale_order = self.env['sale.order'].search([('partner_id', '=', record.partner_id.id)], limit=1)
            if sale_order:
                record.sale_id = sale_order.id
            else:
                record.sale_id = False

    def send_mail_octroyees_grant(self):
        # Envoie un e-mail contenant l'état de la demande.

        template_id = self.env.ref('technocome_module.octroyees_state', raise_if_not_found=False)

        if template_id:
            template = self.env['mail.template'].sudo().browse(template_id.id)
            template.send_mail(self.id, force_send=True)
        else:
            # Gérer le cas où le modèle de courrier électronique n'est pas trouvé
            pass

    # workflow entity
    def attente(self):
        self.write({'state': 'reception_a_compte'})

    def reception_a_compte(self):
        self.write({'state': 'instruire'})

    def instruire(self):
        self.write({'state': 'encours'})

    def encours(self):
        self.write({'state': 'autorisations'})

    def autorisations(self):

        for rec in self:
            rec.write({'state': 'octroyees'})
            if rec.state == 'octroyees':
                rec.send_mail_octroyees_grant()
        self.write({'state': 'octroyees'})

    def octroyees(self):
        for rec in self:
            rec.write({'state': 'planifiee'})
    def planifiee(self):
        for rec in self:
            rec.write({'state': 'effectuee'})
    def effectuee(self):
        for rec in self:
            rec.write({'state': 'subvention en cours'})
    def subvention_en_cours(self):
        for rec in self:
            rec.write({'state': 'subvention finalisee'})
    def subvention_finalisee(self):
        for rec in self:
            rec.write({'state': 'subvention finalisee'})