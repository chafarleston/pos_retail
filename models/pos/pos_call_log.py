# -*- coding: utf-8 -*-
from odoo import api, models, fields
import odoo
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import json
import logging

_logger = logging.getLogger(__name__)

class pos_call_log(models.Model):
    _rec_name = "call_model"
    _name = "pos.call.log"
    _description = "Log datas of pos sessions"

    min_id = fields.Integer('Min Id', required=1, index=True, readonly=1)
    max_id = fields.Integer('Max Id', required=1, index=True, readonly=1)
    call_domain = fields.Char('Domain', required=1,index=True, readonly=1)
    call_results = fields.Char('Results', readonly=1)
    call_model = fields.Char('Model', required=1, index=True, readonly=1)
    call_fields = fields.Char('Fields', index=True, readonly=1)
    active = fields.Boolean('Active', default=True)
    write_date = fields.Datetime('Write date', readonly=1)

    def covert_datetime(self, model, datas):
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
        return datas
    
    @api.multi
    def refresh_call_logs(self):
        cache_database_object = self.env['pos.cache.database']
        logs = self.search([])
        for log in logs:
            call_domain = log.call_domain.replace('true', 'True')
            call_domain = call_domain.replace('false', 'False')
            domains = eval(call_domain)
            for domain in domains:
                if domain and domain[2] == 'true':
                    domain[2] = True
                if domain and domain[2] == 'false':
                    domain[2] = False
            record_ids = self.env[log.call_model].with_context(prefetch_fields=False).sudo().search(domains)
            results = record_ids.sudo().read(eval(log.call_fields))
            version_info = odoo.release.version_info[0]
            if version_info == 12:
                all_fields = self.env[log.call_model].fields_get()
                if all_fields:
                    for result in results:
                        for field, value in result.items():
                            if field == 'model':
                                continue
                            if all_fields[field] and all_fields[field]['type'] in ['date', 'datetime'] and value:
                                result[field] = value.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            log.write({
                'call_results': json.dumps(results)
            })
            cacheds = cache_database_object.search([
                ('res_id', 'in', [record.id for record in record_ids]),
                ('res_model', '=', log.call_model)
            ])
            cacheds.unlink()
        self.env['pos.cache.database'].search([]).unlink()
        return True



