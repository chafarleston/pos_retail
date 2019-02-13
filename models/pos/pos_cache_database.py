# -*- coding: utf-8 -*-
from odoo import api, models, fields, registry
import json
import ast
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import odoo
import logging

_logger = logging.getLogger(__name__)

class pos_cache_database(models.Model):
    _name = "pos.cache.database"
    _description = "Management POS database"
    _rec_name = "res_id"

    res_id = fields.Char('Res Id')
    res_model = fields.Char('Res Model')
    deleted = fields.Boolean('Deleted', default=0)
    updated_date = fields.Datetime('Last updated date', readonly=1)
    
    @api.model
    def create(self, vals):
        vals['updated_date'] = fields.Datetime.now()
        return super(pos_cache_database, self).create(vals)

    @api.model
    def write(self, vals):
        vals['updated_date'] = fields.Datetime.now()
        return super(pos_cache_database, self).write(vals)

    @api.model
    def get_datas_backend_modified(self, updated_date):
        records = self.sudo().search([('updated_date', '>', updated_date)])
        results = []
        if records:
            for record in records:
                try:
                    val = self.env[record.res_model].browse(int(record.res_id)).get_data()
                    if record.deleted:
                        val['deleted'] = True
                        val['id'] = int(record.res_id)
                    val['write_date'] = record.updated_date
                    results.append(val)
                except:
                    val['deleted'] = True
                    val['id'] = int(record.res_id)
                    val['write_date'] = record.updated_date
                    results.append(val)
        return results

    @api.model
    def get_stock_datas(self, location_id, product_need_update_onhand=[]):
        values = {}
        product_object = self.env['product.product'].sudo()
        if not product_need_update_onhand:
            datas = product_object.with_context({'location' : location_id}).search_read(
                [('type', '=', 'product'), ('available_in_pos', '=', True)], ['qty_available'])
        else:
            datas = product_object.with_context({'location' : location_id}).search_read(
                [('id', 'in', product_need_update_onhand)],
                ['name', 'qty_available', 'default_code'])
        for data in datas:
            values[data['id']] = data['qty_available']
        return values

    @api.multi
    def get_fields_by_model(self, model_name):
        params = self.env['ir.config_parameter'].sudo().get_param(model_name)
        if not params:
            list_fields = self.env[model_name].fields_get()
            fields_load = []
            for k, v in list_fields.items():
                if v['type'] not in ['one2many', 'binary']:
                    fields_load.append(k)
            return fields_load
        else:
            params = ast.literal_eval(params)
            return params.get('fields', [])

    @api.multi
    def get_domain_by_model(self, model_name):
        params = self.env['ir.config_parameter'].sudo().get_param(model_name)
        if not params:
            return []
        else:
            params = ast.literal_eval(params)
            return params.get('domain', [])

    @api.model
    def insert_data(self, datas, model, first_install=False):
        if type(model) == list:
            return False
        all_fields = self.env[model].fields_get()
        version_info = odoo.release.version_info[0]
        if version_info == 12:
            if all_fields:
                for data in datas:
                    for field, value in data.items():
                        if field == 'model':
                            continue
                        if all_fields[field] and all_fields[field]['type'] in ['date', 'datetime'] and value:
                            data[field] = value.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if first_install:
            for data in datas:
                self.create({
                    'res_id': str(data['id']),
                    'res_model': model,
                })
        else:
            for data in datas:
                last_caches = self.search([('res_id', '=', str(data['id'])), ('res_model', '=', model)])
                if last_caches:
                    last_caches.write({
                        'updated_date': fields.Datetime.now(),
                    })
                else:
                    self.create({
                        'res_id': str(data['id']),
                        'res_model': model,
                    })
        return True

    def sync_to_pos(self, data):
        if data['model'] == 'product.product':
            data['price'] = data['list_price']
        sessions = self.env['pos.session'].sudo().search([
            ('state', '=', 'opened')
        ])
        self.insert_data([data], data['model'])
        for session in sessions:
            self.env['bus.bus'].sendmany(
                [[(self.env.cr.dbname, 'pos.sync.data', session.user_id.id), data]])
        return True

    @api.model
    def remove_record(self, data):
        self.search([('res_id', '=', str(data['id'])), ('res_model', '=', data['model'])]).write({
            'deleted': True
        })
        sessions = self.env['pos.session'].sudo().search([
            ('state', '=', 'opened')
        ])
        data['deleted'] = True
        for session in sessions:
            self.env['bus.bus'].sendmany(
                [[(self.env.cr.dbname, 'pos.sync.data', session.user_id.id), data]])
        return True

    @api.model
    def save_parameter_models_load(self, model_datas):
        for model_name, value in model_datas.items():
            self.env['ir.config_parameter'].sudo().set_param(model_name, value)
        return True
