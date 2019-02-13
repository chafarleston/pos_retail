# -*- coding: utf-8 -*-
from odoo import fields, api, models

import logging
import base64
import json

_logger = logging.getLogger(__name__)


class stock_location(models.Model):
    _inherit = "stock.location"


    #
    # @api.multi
    # def refresh_stocks(self):
    #     _logger.info('begin refresh_stocks')
    #     locations = self.search([('usage', '=', 'internal')])
    #     for location in locations:
    #         stocks = {}
    #         datas = self.env['product.template'].with_context(location=location.id).search_read(
    #             [('type', '=', 'product'), ('available_in_pos', '=', True)],
    #             ['name', 'qty_available', 'default_code'])
    #         for data in datas:
    #             products = self.env['product.product'].search([('product_tmpl_id', '=', data['id'])])
    #             if products:
    #                 stocks[products[0].id] = data['qty_available']
    #         if stocks:
    #             stocks = {
    #                 'stocks': base64.encodestring(json.dumps(stocks).encode('utf-8')),
    #             }
    #             location.write(stocks)
    #         else:
    #             location.write({
    #                 'stocks': None
    #             })
    #     _logger.info('end refresh_stocks')
    #     return True



