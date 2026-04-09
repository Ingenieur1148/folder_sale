# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class QuotePortal(CustomerPortal):

    # ===================== LISTE DES DEVIS =====================
    @http.route(['/my/quotes', '/my/quotes/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_quotes(self, page=1, sortby='date', search='', **kw):

        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order'].sudo()

        domain = [('partner_id', '=', partner.id)]

        if search:
            domain += [('name', 'ilike', search)]

        sortings = {
            'date': {'label': 'Date', 'order': 'date_order desc'},
            'name': {'label': 'Reference', 'order': 'name asc'},
        }

        order = sortings[sortby]['order']

        total = SaleOrder.search_count(domain)

        pager = portal_pager(
            url="/my/quotes",
            total=total,
            page=page,
            step=10,
            url_args={'sortby': sortby, 'search': search}
        )

        orders = SaleOrder.search(
            domain,
            order=order,
            limit=10,
            offset=pager['offset']
        )

        values = {
            'orders': orders,
            'page_name': 'quotes',
            'pager': pager,
            'search': search,
            'sortby': sortby,
            'searchbar_sortings': sortings,
        }

        return request.render('portal_quotes.portal_my_quotes', values)

    # ===================== DETAIL DEVIS =====================
    @http.route(['/my/quote/<int:order_id>'], type='http', auth='user', website=True)
    def portal_quote_detail(self, order_id, **kw):
        order = request.env['sale.order'].sudo().browse(order_id)

        if not order.exists():
            return request.redirect('/my')

        if order.partner_id != request.env.user.partner_id:
            return request.redirect('/my')

        # Abonne le partenaire comme follower
        order.sudo().message_subscribe([request.env.user.partner_id.id])

        values = {
            'sale_quotation': order,
            'page_name': 'quote_form',
            'token': order.access_token,
        }
        return request.render('portal_quotes.portal_quote_template', values)

    @http.route(['/my/quote/pdf/<int:order_id>'], type='http', auth='user', website=True)
    def download_quote_pdf(self, order_id, **kw):
        order = request.env['sale.order'].sudo().browse(order_id)
        if not order.exists():
            return request.redirect('/my')
        if order.partner_id != request.env.user.partner_id:
            return request.redirect('/my')
        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'objetdesign_report_template.print_devis_template',
            [order.id]
        )
        return request.make_response(pdf, [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', f'attachment; filename=Quotation_{order.name}.pdf')
        ])