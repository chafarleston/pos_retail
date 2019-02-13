# -*- coding: utf-8 -*-
from odoo import fields, api, models

import logging
_logger = logging.getLogger(__name__)


class stock_move(models.Model):
    _inherit = "stock.move"

    @api.model
    def create(self, vals):
        """
        if move create from pos order line
        and pol have uom ID and pol uom ID difference with current move
        we'll re-update product_uom of move
        FOR linked stock on hand of product
        """
        move = super(stock_move, self).create(vals)
        order_lines = self.env['pos.order.line'].search([
            ('name', '=', move.name),
            ('product_id', '=', move.product_id.id),
            ('qty', '=', move.product_uom_qty)
        ])
        for line in order_lines:
            if line.uom_id and line.uom_id != move.product_uom:
                move.write({
                    'product_uom': line.uom_id.id
                })
        move.sync_stock_to_pos_sessions()
        return move

    @api.multi
    def write(self, vals):
        parent = super(stock_move, self).write(vals)
        for move in self:
            move.sync_stock_to_pos_sessions()
        return parent

    @api.multi
    def unlink(self):
        parent = super(stock_move, self).unlink()
        for move in self:
            move.sync_stock_to_pos_sessions()
        return parent

    @api.model
    def sync_stock_to_pos_sessions(self):
        sessions = self.env['pos.session'].sudo().search([
            ('state', '=', 'opened')
        ])
        for session in sessions:
            self.env['bus.bus'].sendmany(
                [[(self.env.cr.dbname, 'pos.sync.stock', session.user_id.id), [self.product_id.id]]])
        return True

class stock_move_line(models.Model): #v11 only, dont merge to v10

    _inherit = "stock.move.line"

    @api.model
    def create(self, vals):
        """
            * When cashier choice product have tracking is not none
            * And submit to sale order to backend
        """
        if vals.get('move_id', None):
            move = self.env['stock.move'].browse(vals.get('move_id'))
            if move.sale_line_id and move.sale_line_id.lot_id:
                vals.update({'lot_id': move.sale_line_id.lot_id.id})
        return super(stock_move_line, self).create(vals)


