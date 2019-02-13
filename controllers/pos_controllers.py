# -*- coding: utf-8 -*
from odoo.http import request
from odoo.addons.bus.controllers.main import BusController
from odoo.addons.web.controllers.main import DataSet
from odoo import api, http, SUPERUSER_ID
from odoo.addons.web.controllers.main import ensure_db, Home, Session, WebClient
from odoo.addons.point_of_sale.controllers.main import PosController
import json
import logging
import ast
import base64
import werkzeug.utils
import timeit

_logger = logging.getLogger(__name__)

class dataset(DataSet):

    @http.route('/api/pos/install_datas', type='json', auth="user")
    def install_datas(self, model, fields=[], offset=0, limit=False, domain=[], sort=None):
        call_log_object = request.env['pos.call.log']
        min_id = domain[0][2]
        max_id = domain[1][2]
        call_logs = call_log_object.with_context(prefetch_fields=False).search([('call_model', '=', model), ('min_id', '=', min_id), ('max_id', '=', max_id)])
        if call_logs:
            call_log = call_logs[0]
            results = call_log.call_results
            return results
        else:
            record_ids = request.env[model].with_context(prefetch_fields=False).sudo().search(domain, order=sort, limit=limit, offset=offset)
            if 'write_date' not in fields:
                fields.append('write_date')
            results = record_ids.sudo().read(fields)
            results = call_log_object.covert_datetime(model, results)
            vals = {
                'active': True,
                'min_id': min_id,
                'max_id': max_id,
                'call_fields': json.dumps(fields),
                'call_results': json.dumps(results),
                'call_model': model,
                'call_domain': json.dumps(domain),
            }
            call_log_object.create(vals)
            return results

class pos_controller(PosController):

    @http.route('/pos/web', type='http', auth='user')
    def pos_web(self, debug=False, **k):
        session_info = request.env['ir.http'].session_info()
        server_version_info = session_info['server_version_info'][0]
        pos_sessions = None
        if server_version_info == 10:
            pos_sessions = request.env['pos.session'].search([
                ('state', '=', 'opened'),
                ('user_id', '=', request.session.uid),
                ('name', 'not like', '(RESCUE FOR')])
        if server_version_info in [11, 12]:
            pos_sessions = request.env['pos.session'].search([
                ('state', '=', 'opened'),
                ('user_id', '=', request.session.uid),
                ('rescue', '=', False)])
        if not pos_sessions:  # auto directly login odoo to pos
            if request.env.user.pos_config_id:
                request.env.user.pos_config_id.current_session_id = request.env['pos.session'].sudo().create({
                    'user_id': request.env.user.id,
                    'config_id': request.env.user.pos_config_id.id,
                })
                pos_sessions = request.env.user.pos_config_id.current_session_id
                pos_sessions.action_pos_session_open()
        if not pos_sessions:
            return werkzeug.utils.redirect('/web#action=point_of_sale.action_client_pos_menu')
        pos_session = pos_sessions[0]
        pos_session.login()
        session_info['model_ids'] = {
            'product.pricelist.item': {},
            'product.product': {},
            'res.partner': {},
            'account.invoice': {},
            'account.invoice.line': {},
            'pos.order': {},
            'pos.order.line': {},
            'sale.order': {},
            'sale.order.line': {},
        }
        first_install = request.env['ir.config_parameter'].sudo().get_param('pos_retail_first_install')
        if not first_install:
            request.env.cr.execute("DELETE FROM pos_cache_database")
            request.env.cr.commit()
            request.env['ir.config_parameter'].sudo().set_param('pos_retail_first_install', 'Done')
        session_info['currency_id'] = request.env.user.company_id.currency_id.id
        model_list = {
            'product.pricelist.item': 'product_pricelist_item',
            'product.product': 'product_product',
            'res.partner': 'res_partner',
            'account.invoice': 'account_invoice',
            'account.invoice.line': 'account_invoice_line',
            'pos.order': 'pos_order',
            'pos.order.line': 'pos_order_line',
            'sale.order': 'sale_order',
            'sale.order.line': 'sale_order_line',
        }
        for object, table in model_list.items():
            if table == "product.product":
                products = request.env['product.product'].search([('available_in_pos', '=', True)], order="id desc", limit=1)
                if products:
                    session_info['model_ids'][object]['max_id'] = products[0].id
                products = request.env['product.product'].search([('available_in_pos', '=', True)],
                                                                 order="id", limit=1)
                if products:
                    session_info['model_ids'][object]['min_id'] = products[0].id
            else:
                request.env.cr.execute("select min(id) from %s" % table)
                min_ids = request.env.cr.fetchall()
                session_info['model_ids'][object]['min_id'] = min_ids[0][0] if min_ids and min_ids[0] else 1
                request.env.cr.execute("select max(id) from %s" % table)
                max_ids = request.env.cr.fetchall()
                session_info['model_ids'][object]['max_id'] = max_ids[0][0] if max_ids and max_ids[0] else 1
        if pos_session:
            config = pos_session.config_id
            session_info['stock_datas'] = None
            if config.stock_location_id and config.display_onhand and not config.large_stocks:
                session_info['stock_datas'] = request.env['pos.cache.database'].sudo().get_stock_datas(config.stock_location_id.id, [])
        context = {
            'session_info': json.dumps(session_info)
        }
        return request.render('point_of_sale.index', qcontext=context)


class web_login(Home):
    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        response = super(web_login, self).web_login(*args, **kw)
        if request.session.uid:
            user = request.env['res.users'].browse(request.session.uid)
            pos_config = user.pos_config_id
            if pos_config:
                return http.local_redirect('/pos/web/')
        return response


class pos_bus(BusController):

    def _poll(self, dbname, channels, last, options):
        channels = list(channels)
        channels.append((request.db, 'pos.sync.stock', request.uid))
        channels.append((request.db, 'pos.sync.data', request.uid))
        channels.append((request.db, 'pos.bus', request.uid))
        channels.append((request.db, 'pos.indexed_db', request.uid))
        channels.append((request.db, 'pos.install.database', request.uid))
        return super(pos_bus, self)._poll(dbname, channels, last, options)

    @http.route('/pos/update_order/status', type="json", auth="public")
    def bus_update_sale_order(self, status, order_name):
        sales = request.env["sale.order"].sudo().search([('name', '=', order_name)])
        sales.write({'sync_status': status})
        return 1

    @http.route('/pos/sync', type="json", auth="public")
    def send(self, bus_id, messages):
        for message in messages:
            if not message.get('value', None) or not message['value'].get('order_uid', None) or not message[
                'value'].get('action', None):
                continue
            user_send_id = message['user_send_id']
            send = 0
            sessions = request.env['pos.session'].sudo().search([
                ('state', '=', 'opened'),
                ('user_id', '!=', user_send_id)
            ])
            request.env['pos.bus.log'].sudo().create({
                'user_id': user_send_id,
                'bus_id': bus_id,
                'action': message['value'].get('action')
            })
            for session in sessions:
                if session.config_id.bus_id and session.config_id.bus_id.id == bus_id and user_send_id != session.user_id.id:
                    send += 1
                    request.env['bus.bus'].sendmany(
                        [[(request.env.cr.dbname, 'pos.bus', session.user_id.id), json.dumps(message)]])
        return json.dumps({
            'status': 'OK',
            'code': 200
        })
