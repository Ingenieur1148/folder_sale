{
    'name': 'Portal Quotations',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Allow portal users to view and manage their quotations',
    'description': 'Portal Quotations for Odoo 18',
    'author': 'Randa Dev',
    'website': 'https://tonsite.com',
    'license': 'OPL-1',
    'price': 49.99,
    'currency': 'EUR',
    'depends': ['sale', 'portal', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/portal_templates.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
}