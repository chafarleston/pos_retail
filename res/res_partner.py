# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

import logging
import ast

_logger = logging.getLogger(__name__)


class res_partner(models.Model):
    _inherit = "res.partner"

    wallet = fields.Float(digits=(16, 4),
                          compute='_compute_wallet', string='Wallet amount', help='This wallet amount of customer')
    credit = fields.Float(digits=(16, 4),
                          compute='_compute_debit_credit_balance', string='Credit amount')
    debit = fields.Float(digits=(16, 4),
                         compute='_compute_debit_credit_balance', string='Debit amount(used)')
    balance = fields.Float(digits=(16, 4),
                           compute='_compute_debit_credit_balance', string='Balance credit amount(can use)')
    limit_debit = fields.Float('Limit debit', help='Limit credit amount can add to this customer')
    credit_history_ids = fields.One2many('res.partner.credit', 'partner_id', 'Credit histories')

    pos_loyalty_point = fields.Float(compute="_get_point", string='Point')
    pos_loyalty_type = fields.Many2one('pos.loyalty.category', 'Type')
    discount_id = fields.Many2one('pos.global.discount', 'Pos discount')

    @api.model
    def create_from_ui(self, partner):
        _logger.info('begin create_from_ui')
        if partner.get('property_product_pricelist', False):
            partner['property_product_pricelist'] = int(partner['property_product_pricelist'])
        if not partner['property_product_pricelist']:
            del partner['property_product_pricelist']
        for key, value in partner.items():
            if value == "false":
                partner[key] = False
            if value == "true":
                partner[key] = True
        _logger.info(partner)
        return super(res_partner, self).create_from_ui(partner)

    @api.multi
    def _get_point(self):
        for partner in self:
            orders = self.env['pos.order'].search([('partner_id', '=', partner.id)])
            for order in orders:
                partner.pos_loyalty_point += order.plus_point
                partner.pos_loyalty_point -= order.redeem_point

    @api.multi
    @api.depends('credit_history_ids')
    def _compute_debit_credit_balance(self):
        for partner in self:
            partner.credit = 0
            partner.debit = 0
            partner.balance = 0
            credits = partner.credit_history_ids
            for credit in credits:
                if credit.type == 'plus':
                    partner.credit += credit.amount
                if credit.type == 'redeem':
                    partner.debit += credit.amount
            partner.balance = partner.credit + partner.limit_debit - partner.debit
        return True

    @api.multi
    def _compute_wallet(self):
        wallet_journal = self.env['account.journal'].search([
            ('pos_method_type', '=', 'wallet'), ('company_id', '=', self.env.user.company_id.id)])
        wallet_statements = self.env['account.bank.statement'].search(
            [('journal_id', 'in', [j.id for j in wallet_journal])])
        for partner in self:
            partner.wallet = 0
            if wallet_statements:
                self._cr.execute(
                    """SELECT l.partner_id, SUM(l.amount)
                    FROM account_bank_statement_line l
                    WHERE l.statement_id IN %s AND l.partner_id = %s
                    GROUP BY l.partner_id
                    """,
                    (tuple(wallet_statements.ids), partner.id))
                datas = self._cr.fetchall()
                for item in datas:
                    partner.wallet -= item[1]

    def get_data(self):
        cache_obj = self.env['pos.cache.database']
        fields_sale_load = cache_obj.get_fields_by_model(self._inherit)
        data = self.read(fields_sale_load)[0]
        data['model'] = self._inherit
        return data

    @api.model
    def sync(self):
        data = self.get_data()
        self.env['pos.cache.database'].sync_to_pos(data)
        return True

    @api.model
    def create(self, vals):
        partner = super(res_partner, self).create(vals)
        partner.sync()
        return partner

    @api.multi
    def write(self, vals):
        res = super(res_partner, self).write(vals)
        for partner in self:
            if partner and partner.id != None and partner.active:
                partner.sync()
            if partner.active == False:
                data = partner.get_data()
                self.env['pos.cache.database'].remove_record(data)
        return res

    @api.multi
    def unlink(self):
        for record in self:
            data = record.get_data()
            self.env['pos.cache.database'].remove_record(data)
        return super(res_partner, self).unlink()
