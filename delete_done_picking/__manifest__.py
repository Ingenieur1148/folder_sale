{
    'name': 'Delete Done picking',
    'version': '18.0.1.0.0',
    'category': 'Stock/Stock',
    'summary': 'User can delete stock done',
    'description': 'Stock picking for Odoo 18',
    'author': 'Randa Dev',
    'website': '',
    'license': 'OPL-1',
    'price': 29.99,
    'currency': 'EUR',
    'depends': ['web', 'base', 'stock'],
    'data': [
        'views/stock_picking_view.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
}