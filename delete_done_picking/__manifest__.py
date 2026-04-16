# -*- coding: utf-8 -*-
{
    'name': 'Delete Done Picking',
    'version': '1.0',
    'summary': 'Allow deletion of done stock pickings (DANGEROUS)',
    'author': 'Custom',
    'category': 'Inventory',
    'depends': ['stock'],
    'data': [
        'views/stock_picking_view.xml',
    ],
    'installable': True,
    'application': False,
}