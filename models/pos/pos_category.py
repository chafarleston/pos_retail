# -*- coding: utf-8 -*-
from odoo import api, models, fields, registry
import logging

_logger = logging.getLogger(__name__)

class pos_category(models.Model):
    _inherit = "pos.category"
   
    @api.model
    def create(self, vals):
        category = super(pos_category, self).create(vals)
        category.sync()
        return category

    @api.multi
    def write(self, vals):
        res = super(pos_category, self).write(vals)
        for category in self:
            category.sync()
        return res

    @api.multi
    def unlink(self):
        for category in self:
            data = category.get_data()
            self.env['pos.cache.database'].remove_record(data)
        return super(pos_category, self).unlink()

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
