# -*- coding: utf-8 -*-
# from odoo import http


# class WscCustom(http.Controller):
#     @http.route('/wsc_custom/wsc_custom/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wsc_custom/wsc_custom/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('wsc_custom.listing', {
#             'root': '/wsc_custom/wsc_custom',
#             'objects': http.request.env['wsc_custom.wsc_custom'].search([]),
#         })

#     @http.route('/wsc_custom/wsc_custom/objects/<model("wsc_custom.wsc_custom"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wsc_custom.object', {
#             'object': obj
#         })
