# -*- coding: utf-8 -*-
from odoo import api, models, fields, registry
import json
import logging

_logger = logging.getLogger(__name__)

class pos_bus(models.Model):
    _name = "pos.bus"
    _description = "Branch/Store of shops"

    name = fields.Char('Location Name', required=1)
    user_id = fields.Many2one('res.users', string='Sale admin')
    log_ids = fields.One2many('pos.bus.log', 'bus_id', string='Logs')

    @api.model
    def sync_orders(self, config_id, datas):
        config = self.env['pos.config'].sudo().browse(config_id)
        sessions = self.env['pos.session'].sudo().search([
            ('state', '=', 'opened')
        ])
        for session in sessions:
            if session.config_id.user_id and session.config_id.user_id != self.env.user and session.config_id and session.config_id.bus_id and session.config_id.bus_id.id == config.bus_id.id:
                for data in datas:
                    value = {
                        'data': data,
                        'action': 'new_order',
                        'bus_id': config.bus_id.id,
                        'order_uid': data['uid']
                    }
                    _logger.info('Sync order to %s' % session.config_id.user_id.login)
                    self.env['bus.bus'].sendmany(
                        [[(self.env.cr.dbname, 'pos.bus', session.config_id.user_id.id), json.dumps({
                            'user_send_id': self.env.user.id,
                            'value': value
                        })]])


class pos_bus_log(models.Model):
    _name = "pos.bus.log"
    _description = "Transactions of Branch/Store"

    user_id = fields.Many2one('res.users', 'User', required=1, ondelete='cascade')
    bus_id = fields.Many2one('pos.bus', 'Branch/Store', required=1, ondelete='cascade')
    action = fields.Selection([
        ('selected_order', 'Change order'),
        ('new_order', 'Add order'),
        ('unlink_order', 'Remove order'),
        ('line_removing', 'Remove line'),
        ('set_client', 'Set customer'),
        ('trigger_update_line', 'Update line'),
        ('change_pricelist', 'Add pricelist'),
        ('sync_sequence_number', 'Sync sequence order'),
        ('lock_order', 'Lock order'),
        ('unlock_order', 'Unlock order'),
        ('set_line_note', 'Set note'),
        ('set_state', 'Set state'),
        ('order_transfer_new_table', 'Transfer to new table'),
        ('set_customer_count', 'Set guest'),
        ('request_printer', 'Request printer'),
        ('set_note', 'Set note'),
        ('paid_order', 'Paid order')
    ], string='Action', required=1)



