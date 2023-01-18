# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api

logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    invoice_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms',
                                              check_company=True)
    siret = fields.Char('Registre de commerce', size=256)

    @api.model
    def _name_search(self, name, args=None, operator="ilike", limit=100, name_get_uid=None):
        args = args or []
        domain = []

        restrict = self.env.context.get('restrict_types')
        if restrict == 'company':
            domain += ['&', ('is_company', '=', True),
                       ("customer_rank", ">", 0)]

        return self._search(domain+args, limit=limit, access_rights_uid=name_get_uid)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    unity = fields.Char(string='Unity')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    unity = fields.Char(string='Unity')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    family_name = fields.Char(
        string='Family', related='product_id.categ_id.name', readonly=True)
    activity_type_name = fields.Char(string='Activity Type', related='product_id.categ_id.parent_id.name',
                                     readonly=True)
    designation_name = fields.Char(string='Designation')
    unity = fields.Char(string='Unity')
    rate_progress = fields.Float("Rate progress (%)")
    name_custom = fields.Text("Designation Client", required=True)

    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res['designation_name'] = self.name
        #res['unity'] = self.unity
        return res

    @api.model
    def write(self, vals):
        self.ensure_one()

        if 'name_custom' in vals:
            name_custom = vals['name_custom']

            product = self.product_id

            # Update stock.move
            for move in self.move_ids:
                if product == move.product_id:
                    move.update({
                        "description_picking": name_custom
                    })

            # Update pickingout text
            product.update({
                "description_pickingout": name_custom
            })

            # Update sale order line name
            vals['name'] = name_custom
        return super(SaleOrderLine, self).write(vals)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    designation_name = fields.Char(string='Designation')
    unity = fields.Char(string='Unity')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    rate_progress = fields.Float("Rate progress (%)")
    client_order_ref = fields.Char("Bon de commande Client", required="True")
    client_reference = fields.Char("Reference Client")
    sale_order_date = fields.Date(string='Date de la commande', required=True)
    infos_client = fields.Char("Autre infos Client")

    @api.model
    def create(self, vals):
        for line in vals['order_line']:
            line[2]["name"] = line[2]["name_custom"]
            product = self.env['product.product'].search(
                [('id', '=', int(line[2]["product_id"]))])
            product.write({
                'description_pickingout': line[2]["name"]
            })
        res = super(SaleOrder, self).create(vals)
        return res


class ResPartner(models.Model):
    _inherit = 'res.partner'

    zip = fields.Char("Boite Postal")
    others_infos = fields.Char("Autres Infos")
    ref = fields.Char("Référence", compute='_compute_reference')

    @api.depends('name')
    def _compute_reference(self):
        for partner in self:
            if partner.name is not False:
                partner.ref = partner.name[0:3] + str(partner.id)
            else:
                partner.ref = ''


class AccountMove(models.Model):
    _inherit = 'account.move'

    declaration_impots = fields.Boolean('A declarer ?', default=False)
    declaration_date = fields.Datetime(string='Date declaration')
    depot_date = fields.Datetime(string='Date depot')
    sale_order_date = fields.Date(
        string='Date commande', compute='_compute_sale_order_date')
    reception_number = fields.Char(
        "Numero Reception", default="RECEPT", required="True")
    acompte = fields.Boolean("Acompte ?")
    acompte_value = fields.Integer("Montant Acompte (FCFA)")
    infos_client = fields.Char(
        string='Autre infos Client', compute='_compute_infos_client')

    def _compute_sale_order_date(self):
        for account_move in self:
            sale_order_id = account_move.invoice_line_ids.mapped(
                'sale_line_ids').order_id.id
            if sale_order_id:
                sale_order = self.env['sale.order'].search(
                    [('id', '=', sale_order_id)], limit=1)
                account_move.sale_order_date = sale_order.sale_order_date
            else:
                account_move.sale_order_date = ""

    def _compute_infos_client(self):
        for account_move in self:
            sale_order_id = account_move.invoice_line_ids.mapped(
                'sale_line_ids').order_id.id
            if sale_order_id:
                sale_order = self.env['sale.order'].search(
                    [('id', '=', sale_order_id)], limit=1)
                account_move.infos_client = sale_order.infos_client
            else:
                account_move.infos_client = ""


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _get_aggregated_product_quantities(self, **kwargs):
        """ Returns a dictionary of products (key = id+name+description+uom) and corresponding values of interest.

        Allows aggregation of data across separate move lines for the same product. This is expected to be useful
        in things such as delivery reports. Dict key is made as a combination of values we expect to want to group
        the products by (i.e. so data is not lost). This function purposely ignores lots/SNs because these are
        expected to already be properly grouped by line.

        returns: dictionary {product_id+name+description+uom: {product, name, description, qty_done, product_uom}, ...}
        """
        aggregated_move_lines = {}
        for move_line in self:
            name = ""
            if move_line.picking_id.picking_type_code == "outgoing":
                name = move_line.product_id.description_pickingout
                description = move_line.move_id.description_picking
            else:
                name = move_line.product_id.name
                description = move_line.move_id.name
            if description == name or description == move_line.product_id.name:
                description = False
            uom = move_line.product_uom_id
            line_key = str(move_line.product_id.id) + "_" + \
                name + (description or "") + "uom " + str(uom.id)

            if line_key not in aggregated_move_lines:
                aggregated_move_lines[line_key] = {'name': name,
                                                   'description': description,
                                                   'qty_done': move_line.qty_done,
                                                   'product_uom': uom.name,
                                                   'product_uom_rec': uom,
                                                   'product': move_line.product_id}
            else:
                aggregated_move_lines[line_key]['qty_done'] += move_line.qty_done
        return aggregated_move_lines


class StockPicking(models.Model):
    _inherit = "stock.picking"

    delivery_date_custom = fields.Date(
        string='Date de livraison', required="True")


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    order_date_custom = fields.Date(string='Date de commande', required="True")


class StockMoveLine(models.Model):
    _inherit = "stock.move"

    @api.model
    def write(self, vals):
        for line in self:
            # Update pickingout text
            product = line.product_id
            product.update({
                "description_pickingout": line.description_picking
            })
        return super(StockMoveLine, self).write(vals)
