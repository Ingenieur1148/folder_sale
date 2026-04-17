{
    'name': 'Acompte in Purchase Order',
    'version': '18.0.1.0.0',
    'category': 'Stock/Stock',
    'summary': 'User can do the acompte purchase order',
    'description': 'Purchase order for Odoo 18',
    'author': 'Randa Dev',
    'website': '',
    'license': 'OPL-1',
    'price': 29.99,
    'currency': 'EUR',
    'depends': ['web', 'base', 'purchase','account'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_invoice_popup_view.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
}