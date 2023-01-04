# -*- coding: utf-8 -*-
{
    'name': "wsc_custom",

    'summary': """
        Add custom functionnalites to Inventory, Sales, etc. modules""",

    'description': """
        Add custom functionnalites to Inventory, Sales, etc. modules
    """,

    'author': "NET2S",
    'website': "https://www.net2s.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Inventory',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale', 'l10n_fr'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
