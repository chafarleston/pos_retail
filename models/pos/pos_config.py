# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import odoo
import logging
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import json

import io
import os
import timeit

try:
    to_unicode = unicode
except NameError:
    to_unicode = str

_logger = logging.getLogger(__name__)


class pos_config_image(models.Model):
    _name = "pos.config.image"
    _description = "Image show to customer screen"

    name = fields.Char('Title', required=1)
    image = fields.Binary('Image', required=1)
    config_id = fields.Many2one('pos.config', 'POS config', required=1)
    description = fields.Text('Description')


class pos_config(models.Model):
    _inherit = "pos.config"

    user_id = fields.Many2one('res.users', 'Assigned to')
    config_access_right = fields.Boolean('Config access right', default=1)
    allow_discount = fields.Boolean('Change discount', default=1)
    allow_qty = fields.Boolean('Change quantity', default=1)
    allow_price = fields.Boolean('Change price', default=1)
    allow_remove_line = fields.Boolean('Remove line', default=1)
    allow_numpad = fields.Boolean('Display numpad', default=1)
    allow_payment = fields.Boolean('Display payment', default=1)
    allow_customer = fields.Boolean('Choice customer', default=1)
    allow_add_order = fields.Boolean('New order', default=1)
    allow_remove_order = fields.Boolean('Remove order', default=1)
    allow_add_product = fields.Boolean('Add line', default=1)

    allow_lock_screen = fields.Boolean('Lock screen',
                                       default=0,
                                       help='When pos sessions start, cashiers required open POS viva pos pass pin (Setting/Users)')

    display_point_receipt = fields.Boolean('Display point / receipt')
    loyalty_id = fields.Many2one('pos.loyalty', 'Loyalty',
                                 domain=[('state', '=', 'running')])

    promotion_ids = fields.Many2many('pos.promotion',
                                     'pos_config_promotion_rel',
                                     'config_id',
                                     'promotion_id',
                                     string='Promotion programs')
    promotion_manual_select = fields.Boolean('Promotion manual choice', default=0)

    create_purchase_order = fields.Boolean('Create PO', default=0)
    create_purchase_order_required_signature = fields.Boolean('Required signature', default=0)
    purchase_order_state = fields.Selection([
        ('confirm_order', 'Auto confirm'),
        ('confirm_picking', 'Auto delivery'),
        ('confirm_invoice', 'Auto invoice'),
    ], 'PO state',
        help='This is state of purchase order will process to',
        default='confirm_invoice')

    sync_sale_order = fields.Boolean('Sync sale orders', default=0)
    sale_order = fields.Boolean('Create Sale order', default=0)
    sale_order_auto_confirm = fields.Boolean('Auto confirm', default=0)
    sale_order_auto_invoice = fields.Boolean('Auto paid', default=0)
    sale_order_auto_delivery = fields.Boolean('Auto delivery', default=0)

    pos_orders_management = fields.Boolean('POS order management', default=0)
    pos_order_period_return_days = fields.Float('Return period days',
                                                help='this is period time for customer can return order',
                                                default=30)
    display_return_days_receipt = fields.Boolean('Display return days receipt', default=0)

    sync_pricelist = fields.Boolean('Sync prices list', default=0)

    display_onhand = fields.Boolean('Show qty available product', default=1,
                                    help='Display quantity on hand all products on pos screen')
    large_stocks = fields.Boolean('Large stock', help='If count products bigger than 100,000 rows, please check it')
    allow_order_out_of_stock = fields.Boolean('Allow out-of-stock', default=1,
                                              help='If checked, allow cashier can add product have out of stock')
    allow_of_stock_approve_by_admin = fields.Boolean('Approve allow of stock',
                                                     help='Allow manager approve allow of stock')

    print_voucher = fields.Boolean('Print vouchers', help='Reprint last vouchers', default=1)
    scan_voucher = fields.Boolean('Scan voucher', default=0)
    expired_days_voucher = fields.Integer('Expired days of voucher', default=30,
                                          help='Total days keep voucher can use, if out of period days from create date, voucher will expired')

    sync_multi_session = fields.Boolean('Sync multi session', default=0)
    bus_id = fields.Many2one('pos.bus', string='Branch/store')
    display_person_add_line = fields.Boolean('Display information line', default=0,
                                             help="When you checked, on pos order lines screen, will display information person created order (lines) Eg: create date, updated date ..")

    quickly_payment = fields.Boolean('Quickly payment', default=0)
    internal_transfer = fields.Boolean('Internal transfer', default=0,
                                       help='Go Inventory and active multi warehouse and location')
    internal_transfer_auto_validate = fields.Boolean('Internal transfer auto validate', default=0)

    discount = fields.Boolean('Global discount', default=0)
    discount_ids = fields.Many2many('pos.global.discount',
                                    'pos_config_pos_global_discount_rel',
                                    'config_id',
                                    'discount_id',
                                    'Global discounts')

    is_customer_screen = fields.Boolean('Is customer screen')
    delay = fields.Integer('Delay time', default=3000)
    slogan = fields.Char('Slogan', help='This is message will display on screen of customer')
    image_ids = fields.One2many('pos.config.image', 'config_id', 'Images')

    tooltip = fields.Boolean('Product tooltip', default=0)
    discount_limit = fields.Boolean('Discount limit', default=0)
    discount_limit_amount = fields.Float('Discount limit amount', default=10)

    multi_currency = fields.Boolean('Multi currency', default=0)
    multi_currency_update_rate = fields.Boolean('Update rate', default=0)

    notify_alert = fields.Boolean('Notify alert',
                                  help='Turn on/off notification alert on POS sessions.',
                                  default=0)
    return_products = fields.Boolean('Return orders',
                                     help='Allow cashier return orders, return products',
                                     default=0)
    receipt_without_payment_template = fields.Selection([
        ('none', 'None'),
        ('display_price', 'Display price'),
        ('not_display_price', 'Not display price')
    ], default='not_display_price', string='Receipt without payment template')
    lock_order_printed_receipt = fields.Boolean('Lock order printed receipt', default=0)
    staff_level = fields.Selection([
        ('manual', 'Manual config'),
        ('marketing', 'Marketing'),
        ('waiter', 'Waiter'),
        ('cashier', 'Cashier'),
        ('manager', 'Manager')
    ], string='Staff level', default='manual')

    validate_payment = fields.Boolean('Validate payment')
    validate_remove_order = fields.Boolean('Validate remove order')
    validate_change_minus = fields.Boolean('Validate pressed +/-')
    validate_quantity_change = fields.Boolean('Validate quantity change')
    validate_price_change = fields.Boolean('Validate price change')
    validate_discount_change = fields.Boolean('Validate discount change')
    validate_close_session = fields.Boolean('Validate close session')
    apply_validate_return_mode = fields.Boolean('Validate return mode',
                                                help='If checked, only applied validate when return order', default=1)

    print_user_card = fields.Boolean('Print user card')

    product_operation = fields.Boolean('Product Operation', default=0,
                                       help='Allow cashiers add pos categories and products on pos screen')
    quickly_payment_full = fields.Boolean('Quickly payment full')
    quickly_payment_full_journal_id = fields.Many2one('account.journal', 'Payment mode',
                                                      domain=[('journal_user', '=', True)])
    daily_report = fields.Boolean('Daily report', default=0)
    note_order = fields.Boolean('Note order', default=0)
    note_orderline = fields.Boolean('Note order line', default=0)
    signature_order = fields.Boolean('Signature order', default=0)
    quickly_buttons = fields.Boolean('Quickly Actions', default=0)
    display_amount_discount = fields.Boolean('Display amount discount', default=0)

    booking_orders = fields.Boolean('Booking orders', default=0)
    booking_orders_required_cashier_signature = fields.Boolean('Book order required sessions signature',
                                                               help='Checked if need required pos seller signature',
                                                               default=0)
    booking_orders_alert = fields.Boolean('Alert when new order coming', default=0)
    delivery_orders = fields.Boolean('Delivery orders',
                                     help='Pos clients can get booking orders and delivery orders',
                                     default=0)
    booking_orders_display_shipping_receipt = fields.Boolean('Display shipping on receipt', default=0)

    display_tax_orderline = fields.Boolean('Display tax orderline', default=0)
    display_tax_receipt = fields.Boolean('Display tax receipt', default=0)
    display_fiscal_position_receipt = fields.Boolean('Display fiscal position on receipt', default=0)

    display_image_orderline = fields.Boolean('Display image order line', default=0)
    display_image_receipt = fields.Boolean('Display image receipt', default=0)
    duplicate_receipt = fields.Boolean('Duplicate Receipt')
    print_number = fields.Integer('Print number', help='How many number receipt need to print at printer ?', default=0)

    lock_session = fields.Boolean('Lock session', default=0)
    category_wise_receipt = fields.Boolean('Category wise receipt', default=0)

    management_invoice = fields.Boolean('Management Invoice', default=0)
    invoice_journal_ids = fields.Many2many(
        'account.journal',
        'pos_config_invoice_journal_rel',
        'config_id',
        'journal_id',
        'Accounting Invoice Journal',
        domain=[('type', '=', 'sale')],
        help="Accounting journal use for create invoices.")
    send_invoice_email = fields.Boolean('Send email invoice', help='Help cashier send invoice to email of customer',
                                        default=0)
    lock_print_invoice_on_pos = fields.Boolean('Lock print invoice',
                                               help='Lock print pdf invoice when clicked button invoice', default=0)
    pos_auto_invoice = fields.Boolean('Auto create invoice',
                                      help='Automatic create invoice if order have client',
                                      default=0)
    receipt_invoice_number = fields.Boolean('Add invoice on receipt', help='Show invoice number on receipt header',
                                            default=0)
    receipt_customer_vat = fields.Boolean('Add vat customer on receipt',
                                          help='Show customer VAT(TIN) on receipt header', default=0)
    auto_register_payment = fields.Boolean('Auto invocie register payment', default=0)

    fiscal_position_auto_detect = fields.Boolean('Fiscal position auto detect', default=0)

    display_sale_price_within_tax = fields.Boolean('Display sale price within tax', default=0)
    display_cost_price = fields.Boolean('Display product cost price', default=0)
    display_product_ref = fields.Boolean('Display product ref', default=0)
    multi_location = fields.Boolean('Multi location', default=0)
    product_view = fields.Selection([
        ('box', 'Box view'),
        ('list', 'List view'),
    ], default='box', string='View of products screen', required=1)

    ticket_font_size = fields.Integer('Ticket font size', default=12)
    customer_default_id = fields.Many2one('res.partner', 'Customer default')
    medical_insurance = fields.Boolean('Medical insurance', default=0)
    discount_each_line = fields.Boolean('Discount each line')
    manager_validate = fields.Boolean('Manager can validate')
    manager_user_id = fields.Many2one('res.users', 'Manager validate')
    set_guest = fields.Boolean('Set guest', default=0)
    reset_sequence = fields.Boolean('Reset sequence order', default=0)
    update_tax = fields.Boolean('Modify tax', default=0, help='Cashier can change tax of order line')
    subtotal_tax_included = fields.Boolean('Show Tax-Included Prices',
                                           help='When checked, subtotal of line will display amount have tax-included')
    cash_out = fields.Boolean('Take money out', default=0, help='Allow cashiers take money out')
    cash_in = fields.Boolean('Push money in', default=0, help='Allow cashiers input money in')
    min_length_search = fields.Integer('Min character length search', default=3,
                                       help='Allow auto suggestion items when cashiers input on search box')
    review_receipt_before_paid = fields.Boolean('Review receipt before paid', help='Show receipt before paid order',
                                                default=1)
    keyboard_event = fields.Boolean('Keyboard event', default=0, help='Allow cashiers use shortcut keyboard')
    multi_variant = fields.Boolean('Multi variant', default=0,
                                   help='Allow cashiers change variant of order lines on pos screen')
    switch_user = fields.Boolean('Switch user', default=0, help='Allow cashiers switch to another cashier')
    change_unit_of_measure = fields.Boolean('Change unit of measure', default=0,
                                            help='Allow cashiers change unit of measure of order lines')
    print_last_order = fields.Boolean('Print last receipt', default=0, help='Allow cashiers print last receipt')
    close_session = fields.Boolean('Close session', help='When cashiers click close pos, auto log out of system',
                                   default=0)
    display_image_product = fields.Boolean('Display image product', default=1,
                                           help='Allow hide/display product images on pos screen')
    printer_on_off = fields.Boolean('On/Off printer', help='Help cashier turn on/off printer viva posbox', default=0)
    check_duplicate_email = fields.Boolean('Check duplicate email', default=0)
    check_duplicate_phone = fields.Boolean('Check duplicate phone', default=0)
    hide_country = fields.Boolean('Hide country', default=0)
    hide_barcode = fields.Boolean('Hide barcode', default=0)
    hide_tax = fields.Boolean('Hide tax', default=0)
    hide_pricelist = fields.Boolean('Hide pricelists', default=0)
    hide_supplier = fields.Boolean('Hide suppiers', default=1)
    auto_remove_line = fields.Boolean('Auto remove line',
                                      default=1,
                                      help='When cashier set quantity of line to 0, line auto remove not keep line with qty is 0')
    chat = fields.Boolean('Chat message', default=0, help='Allow chat, discuss between pos sessions')
    add_tags = fields.Boolean('Add tags line', default=0, help='Allow cashiers add tags to order lines')
    add_notes = fields.Boolean('Add notes line', default=0, help='Allow cashiers add notes to order lines')
    add_sale_person = fields.Boolean('Add sale person', default=0)
    logo = fields.Binary('Logo of store')
    paid_full = fields.Boolean('Allow paid full', default=0,
                               help='Allow cashiers click one button, do payment full order')
    paid_partial = fields.Boolean('Allow partial payment', default=0, help='Allow cashiers do partial payment')
    backup = fields.Boolean('Backup/Restore orders', default=0,
                            help='Allow cashiers backup and restore orders on pos screen')
    backup_orders = fields.Text('Backup orders')
    change_logo = fields.Boolean('Change logo', default=1, help='Allow cashiers change logo of shop on pos screen')
    management_session = fields.Boolean('Management session', default=0)
    barcode_receipt = fields.Boolean('Barcode receipt', default=0)

    hide_mobile = fields.Boolean('Hide mobile', default=1)
    hide_phone = fields.Boolean('Hide phone', default=1)
    hide_email = fields.Boolean('Hide email', default=1)
    update_client = fields.Boolean('Update client',
                                   help='Uncheck if you dont want cashier change customer information on pos')
    add_client = fields.Boolean('Add client', help='Uncheck if you dont want cashier add new customers on pos')
    remove_client = fields.Boolean('Remove client', help='Uncheck if you dont want cashier remove customers on pos')
    mobile_responsive = fields.Boolean('Mobile responsive', default=0)

    hide_amount_total = fields.Boolean('Hide amount total', default=1)
    hide_amount_taxes = fields.Boolean('Hide amount taxes', default=1)


    report_no_of_report = fields.Integer(string="No.of Copy Receipt", default=1)
    report_signature = fields.Boolean(string="Report Signature", default=1)

    report_product_summary = fields.Boolean(string="Report Product Summary", default=1)
    report_product_current_month_date = fields.Boolean(string="Report Current Month", default=1)

    report_order_summary = fields.Boolean(string='Report Order Summary', default=1)
    report_order_current_month_date = fields.Boolean(string="Report Current Month", default=1)

    report_payment_summary = fields.Boolean(string="Report Payment Summary", default=1)
    report_payment_current_month_date = fields.Boolean(string="Payment Current Month", default=1)

    active_product_sort_by = fields.Boolean('Active product sort by', default=1)
    default_product_sort_by = fields.Selection([
        ('a_z', 'Sort from A to Z'),
        ('z_a', 'Sort from Z to A'),
        ('low_price', 'Sort from low to high price'),
        ('high_price', 'Sort from high to low price'),
        ('pos_sequence', 'Product pos sequence')
    ], string='Default sort by', default='a_z')

    @api.model
    def switch_mobile_mode(self, config_id, vals):
        if vals.get('mobile_responsive') == True:
            vals['product_view'] = 'box'
        return self.browse(config_id).sudo().write(vals)

    @api.multi
    def remove_database(self):
        for config in self:
            sessions = self.env['pos.session'].search([('config_id', '=', config.id)])
            for session in sessions:
                self.env['bus.bus'].sendmany(
                    [[(self.env.cr.dbname, 'pos.indexed_db', session.user_id.id), json.dumps({
                        'db': self.env.cr.dbname
                    })]])
            self.env['pos.cache.database'].search([]).unlink()
            self.env['pos.call.log'].search([]).unlink()
            return {
                'type': 'ir.actions.act_url',
                'url': '/pos/web/',
                'target': 'self',
            }

    @api.multi
    def remove_caches(self):
        for config in self:
            sessions = self.env['pos.session'].search([('config_id', '=', config.id)])
            for session in sessions:
                self.env['bus.bus'].sendmany(
                    [[(self.env.cr.dbname, 'pos.indexed_db', session.user_id.id), json.dumps({
                        'db': self.env.cr.dbname
                    })]])
                if session.state != 'closed':
                    session.action_pos_session_closing_control()
            return {
                'type': 'ir.actions.act_url',
                'url': '/pos/web/',
                'target': 'self',
            }

    @api.model
    def store_cached_file(self, datas):
        start = timeit.default_timer()
        _logger.info('==> begin cached_file')
        os.chdir(os.path.dirname(__file__))
        path = os.getcwd()
        file_name = path + '/pos.json'
        if os.path.exists(file_name):
            os.remove(file_name)
        with io.open(file_name, 'w', encoding='utf8') as outfile:
            str_ = json.dumps(datas, indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False)
            outfile.write(to_unicode(str_))
        stop = timeit.default_timer()
        _logger.info(stop - start)
        return True

    @api.model
    def get_cached_file(self):
        start = timeit.default_timer()
        _logger.info('==> begin get_cached_file')
        os.chdir(os.path.dirname(__file__))
        path = os.getcwd()
        file_name = path + '/pos.json'
        if not os.path.exists(file_name):
            return False
        else:
            with open(file_name) as f:
                datas = json.load(f)
                stop = timeit.default_timer()
                _logger.info(stop - start)
                return datas

    def get_fields_by_model(self, model):
        all_fields = self.env[model].fields_get()
        fields_list = []
        for field, value in all_fields.items():
            if field == 'model' or all_fields[field]['type'] in ['one2many', 'binary']:
                continue
            else:
                fields_list.append(field)
        return fields_list

    @api.model
    def install_data(self, model_name=None, min_id=0, max_id=1999):
        cache_obj = self.env['pos.cache.database'].with_context(prefetch_fields=False)
        log_obj = self.env['pos.call.log'].with_context(prefetch_fields=False)
        domain = [('id', '>=', min_id), ('id', '<=', max_id)]
        if model_name == 'product.product':
            domain.append(('available_in_pos', '=', True))
        field_list = cache_obj.get_fields_by_model(model_name)
        self.env.cr.execute("select id from pos_call_log where min_id=%s and max_id=%s and call_model='%s'" % (
            min_id, max_id, model_name))
        old_logs = self.env.cr.fetchall()
        datas = None
        if len(old_logs) == 0:
            _logger.info('installing %s from %s to %s' % (model_name, min_id, max_id))
            datas = self.env[model_name].with_context(prefetch_fields=False).search_read(domain, field_list)
            version_info = odoo.release.version_info[0]
            if version_info == 12:
                all_fields = self.env[model_name].fields_get()
                for data in datas:
                    for field, value in data.items():
                        if field == 'model':
                            continue
                        if all_fields[field] and all_fields[field]['type'] in ['date',
                                                                               'datetime'] and value:
                            data[field] = value.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            vals = {
                'active': True,
                'min_id': min_id,
                'max_id': max_id,
                'call_fields': json.dumps(field_list),
                'call_results': json.dumps(datas),
                'call_model': model_name,
                'call_domain': json.dumps(domain),
            }
            log_obj.create(vals)
        else:
            old_log_id = old_logs[0][0]
            old_log = log_obj.browse(old_log_id)
            datas = old_log.call_results
        self.env.cr.commit()
        return datas

    @api.onchange('lock_print_invoice_on_pos')
    def _onchange_lock_print_invoice_on_pos(self):
        if self.lock_print_invoice_on_pos == True:
            self.receipt_invoice_number = False
            self.send_invoice_email = True
        else:
            self.receipt_invoice_number = True
            self.send_invoice_email = False

    @api.onchange('receipt_invoice_number')
    def _onchange_receipt_invoice_number(self):
        if self.receipt_invoice_number == True:
            self.lock_print_invoice_on_pos = False
        else:
            self.lock_print_invoice_on_pos = True

    @api.onchange('pos_auto_invoice')
    def _onchange_pos_auto_invoice(self):
        if self.pos_auto_invoice == True:
            self.iface_invoicing = True
        else:
            self.iface_invoicing = False

    @api.onchange('staff_level')
    def on_change_staff_level(self):
        if self.staff_level and self.staff_level == 'manager':
            self.lock_order_printed_receipt = False

    @api.multi
    def write(self, vals):
        if vals.get('allow_discount', False) or vals.get('allow_qty', False) or vals.get('allow_price', False):
            vals['allow_numpad'] = True
        if vals.get('expired_days_voucher', None) and vals.get('expired_days_voucher') < 0:
            raise UserError('Expired days of voucher could not smaller than 0')
        if vals.get('management_session', False):
            for config in self:
                if not config.default_cashbox_lines_ids and not config.cash_control:
                    raise UserError('Please go to Cash control and add Default Opening')
        return super(pos_config, self).write(vals)

    @api.model
    def create(self, vals):
        if vals.get('allow_discount', False) or vals.get('allow_qty', False) or vals.get('allow_price', False):
            vals['allow_numpad'] = True
        if vals.get('expired_days_voucher', 0) < 0:
            raise UserError('Expired days of voucher could not smaller than 0')
        config = super(pos_config, self).create(vals)
        if config.management_session and not config.default_cashbox_lines_ids and not config.cash_control:
            raise UserError('Please go to Cash control and add Default Opening')
        return config

    def init_wallet_journal(self):
        Journal = self.env['account.journal']
        user = self.env.user
        wallet_journal = Journal.sudo().search([
            ('code', '=', 'UWJ'),
            ('company_id', '=', user.company_id.id),
        ])
        if wallet_journal:
            return wallet_journal.sudo().write({
                'pos_method_type': 'wallet'
            })
        Account = self.env['account.account']
        wallet_account_old_version = Account.sudo().search([
            ('code', '=', 'AUW'), ('company_id', '=', user.company_id.id)])
        if wallet_account_old_version:
            wallet_account = wallet_account_old_version[0]
        else:
            wallet_account = Account.sudo().create({
                'name': 'Account wallet',
                'code': 'AUW',
                'user_type_id': self.env.ref('account.data_account_type_current_assets').id,
                'company_id': user.company_id.id,
                'note': 'code "AUW" auto give wallet amount of customers',
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'account_use_wallet' + str(user.company_id.id),
                'model': 'account.account',
                'module': 'pos_retail',
                'res_id': wallet_account.id,
                'noupdate': True,  # If it's False, target record (res_id) will be removed while module update
            })

        wallet_journal_inactive = Journal.sudo().search([
            ('code', '=', 'UWJ'),
            ('company_id', '=', user.company_id.id),
            ('pos_method_type', '=', 'wallet')
        ])
        if wallet_journal_inactive:
            wallet_journal_inactive.sudo().write({
                'default_debit_account_id': wallet_account.id,
                'default_credit_account_id': wallet_account.id,
                'pos_method_type': 'wallet',
                'sequence': 100,
            })
            wallet_journal = wallet_journal_inactive
        else:
            new_sequence = self.env['ir.sequence'].sudo().create({
                'name': 'Account Default Wallet Journal ' + str(user.company_id.id),
                'padding': 3,
                'prefix': 'UW ' + str(user.company_id.id),
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'journal_sequence' + str(new_sequence.id),
                'model': 'ir.sequence',
                'module': 'pos_retail',
                'res_id': new_sequence.id,
                'noupdate': True,
            })
            wallet_journal = Journal.sudo().create({
                'name': 'Wallet',
                'code': 'UWJ',
                'type': 'cash',
                'pos_method_type': 'wallet',
                'journal_user': True,
                'sequence_id': new_sequence.id,
                'company_id': user.company_id.id,
                'default_debit_account_id': wallet_account.id,
                'default_credit_account_id': wallet_account.id,
                'sequence': 100,
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'use_wallet_journal_' + str(wallet_journal.id),
                'model': 'account.journal',
                'module': 'pos_retail',
                'res_id': int(wallet_journal.id),
                'noupdate': True,
            })

        config = self
        config.sudo().write({
            'journal_ids': [(4, wallet_journal.id)],
        })

        statement = [(0, 0, {
            'journal_id': wallet_journal.id,
            'user_id': user.id,
            'company_id': user.company_id.id
        })]
        current_session = config.current_session_id
        current_session.sudo().write({
            'statement_ids': statement,
        })
        return

    def init_voucher_journal(self):
        Journal = self.env['account.journal']
        user = self.env.user
        voucher_journal = Journal.sudo().search([
            ('code', '=', 'VCJ'),
            ('company_id', '=', user.company_id.id),
        ])
        if voucher_journal:
            return voucher_journal.sudo().write({
                'pos_method_type': 'voucher'
            })
        Account = self.env['account.account']
        voucher_account_old_version = Account.sudo().search([
            ('code', '=', 'AVC'), ('company_id', '=', user.company_id.id)])
        if voucher_account_old_version:
            voucher_account = voucher_account_old_version[0]
        else:
            voucher_account = Account.sudo().create({
                'name': 'Account voucher',
                'code': 'AVC',
                'user_type_id': self.env.ref('account.data_account_type_current_assets').id,
                'company_id': user.company_id.id,
                'note': 'code "AVC" auto give voucher histories of customers',
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'account_voucher' + str(user.company_id.id),
                'model': 'account.account',
                'module': 'pos_retail',
                'res_id': voucher_account.id,
                'noupdate': True,  # If it's False, target record (res_id) will be removed while module update
            })

        voucher_journal = Journal.sudo().search([
            ('code', '=', 'VCJ'),
            ('company_id', '=', user.company_id.id),
            ('pos_method_type', '=', 'voucher')
        ])
        if voucher_journal:
            voucher_journal[0].sudo().write({
                'voucher': True,
                'default_debit_account_id': voucher_account.id,
                'default_credit_account_id': voucher_account.id,
                'pos_method_type': 'voucher',
                'sequence': 101,
            })
            voucher_journal = voucher_journal[0]
        else:
            new_sequence = self.env['ir.sequence'].sudo().create({
                'name': 'Account Voucher ' + str(user.company_id.id),
                'padding': 3,
                'prefix': 'AVC ' + str(user.company_id.id),
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'journal_sequence' + str(new_sequence.id),
                'model': 'ir.sequence',
                'module': 'pos_retail',
                'res_id': new_sequence.id,
                'noupdate': True,
            })
            voucher_journal = Journal.sudo().create({
                'name': 'Voucher',
                'code': 'VCJ',
                'type': 'cash',
                'pos_method_type': 'voucher',
                'journal_user': True,
                'sequence_id': new_sequence.id,
                'company_id': user.company_id.id,
                'default_debit_account_id': voucher_account.id,
                'default_credit_account_id': voucher_account.id,
                'sequence': 101,
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'journal_voucher_' + str(voucher_journal.id),
                'model': 'account.journal',
                'module': 'pos_retail',
                'res_id': int(voucher_journal.id),
                'noupdate': True,
            })

        config = self
        config.sudo().write({
            'journal_ids': [(4, voucher_journal.id)],
        })

        statement = [(0, 0, {
            'journal_id': voucher_journal.id,
            'user_id': user.id,
            'company_id': user.company_id.id
        })]
        current_session = config.current_session_id
        current_session.sudo().write({
            'statement_ids': statement,
        })
        return

    def init_credit_journal(self):
        Journal = self.env['account.journal']
        user = self.env.user
        voucher_journal = Journal.sudo().search([
            ('code', '=', 'CJ'),
            ('company_id', '=', user.company_id.id),
        ])
        if voucher_journal:
            return voucher_journal.sudo().write({
                'pos_method_type': 'credit'
            })
        Account = self.env['account.account']
        credit_account_old_version = Account.sudo().search([
            ('code', '=', 'ACJ'), ('company_id', '=', user.company_id.id)])
        if credit_account_old_version:
            credit_account = credit_account_old_version[0]
        else:
            credit_account = Account.sudo().create({
                'name': 'Credit Account',
                'code': 'CA',
                'user_type_id': self.env.ref('account.data_account_type_current_assets').id,
                'company_id': user.company_id.id,
                'note': 'code "CA" give credit payment customer',
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'account_credit' + str(user.company_id.id),
                'model': 'account.account',
                'module': 'pos_retail',
                'res_id': credit_account.id,
                'noupdate': True,  # If it's False, target record (res_id) will be removed while module update
            })

        credit_journal = Journal.sudo().search([
            ('code', '=', 'CJ'),
            ('company_id', '=', user.company_id.id),
            ('pos_method_type', '=', 'credit')
        ])
        if credit_journal:
            credit_journal[0].sudo().write({
                'credit': True,
                'default_debit_account_id': credit_account.id,
                'default_credit_account_id': credit_account.id,
                'pos_method_type': 'credit',
                'sequence': 102,
            })
            credit_journal = credit_journal[0]
        else:
            new_sequence = self.env['ir.sequence'].sudo().create({
                'name': 'Credit account ' + str(user.company_id.id),
                'padding': 3,
                'prefix': 'CA ' + str(user.company_id.id),
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'journal_sequence' + str(new_sequence.id),
                'model': 'ir.sequence',
                'module': 'pos_retail',
                'res_id': new_sequence.id,
                'noupdate': True,
            })
            credit_journal = Journal.sudo().create({
                'name': 'Customer Credit',
                'code': 'CJ',
                'type': 'cash',
                'pos_method_type': 'credit',
                'journal_user': True,
                'sequence_id': new_sequence.id,
                'company_id': user.company_id.id,
                'default_debit_account_id': credit_account.id,
                'default_credit_account_id': credit_account.id,
                'sequence': 102,
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'credit_journal_' + str(credit_journal.id),
                'model': 'account.journal',
                'module': 'pos_retail',
                'res_id': int(credit_journal.id),
                'noupdate': True,
            })

        config = self
        config.sudo().write({
            'journal_ids': [(4, credit_journal.id)],
        })

        statement = [(0, 0, {
            'journal_id': credit_journal.id,
            'user_id': user.id,
            'company_id': user.company_id.id
        })]
        current_session = config.current_session_id
        current_session.sudo().write({
            'statement_ids': statement,
        })
        return True

    def init_return_order_journal(self):
        Journal = self.env['account.journal']
        user = self.env.user
        return_journal = Journal.sudo().search([
            ('code', '=', 'ROJ'),
            ('company_id', '=', user.company_id.id),
        ])
        if return_journal:
            return return_journal.sudo().write({
                'pos_method_type': 'return'
            })
        Account = self.env['account.account']
        return_account_old_version = Account.sudo().search([
            ('code', '=', 'ARO'), ('company_id', '=', user.company_id.id)])
        if return_account_old_version:
            return_account = return_account_old_version[0]
        else:
            return_account = Account.sudo().create({
                'name': 'Return Order Account',
                'code': 'ARO',
                'user_type_id': self.env.ref('account.data_account_type_current_assets').id,
                'company_id': user.company_id.id,
                'note': 'code "ARO" give return order from customer',
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'return_account' + str(user.company_id.id),
                'model': 'account.account',
                'module': 'pos_retail',
                'res_id': return_account.id,
                'noupdate': True,  # If it's False, target record (res_id) will be removed while module update
            })

        return_journal = Journal.sudo().search([
            ('code', '=', 'ROJ'),
            ('company_id', '=', user.company_id.id),
        ])
        if return_journal:
            return_journal[0].sudo().write({
                'default_debit_account_id': return_account.id,
                'default_credit_account_id': return_account.id,
                'pos_method_type': 'return'
            })
            return_journal = return_journal[0]
        else:
            new_sequence = self.env['ir.sequence'].sudo().create({
                'name': 'Return account ' + str(user.company_id.id),
                'padding': 3,
                'prefix': 'RA ' + str(user.company_id.id),
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'journal_sequence' + str(new_sequence.id),
                'model': 'ir.sequence',
                'module': 'pos_retail',
                'res_id': new_sequence.id,
                'noupdate': True,
            })
            return_journal = Journal.sudo().create({
                'name': 'Return Order Customer',
                'code': 'ROJ',
                'type': 'cash',
                'pos_method_type': 'return',
                'journal_user': True,
                'sequence_id': new_sequence.id,
                'company_id': user.company_id.id,
                'default_debit_account_id': return_account.id,
                'default_credit_account_id': return_account.id,
                'sequence': 103,
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'return_journal_' + str(return_journal.id),
                'model': 'account.journal',
                'module': 'pos_retail',
                'res_id': int(return_journal.id),
                'noupdate': True,
            })

        config = self
        config.sudo().write({
            'journal_ids': [(4, return_journal.id)],
        })

        statement = [(0, 0, {
            'journal_id': return_journal.id,
            'user_id': user.id,
            'company_id': user.company_id.id
        })]
        current_session = config.current_session_id
        current_session.sudo().write({
            'statement_ids': statement,
        })
        return True

    def init_rounding_journal(self):
        Journal = self.env['account.journal']
        Account = self.env['account.account']
        user = self.env.user
        rounding_journal = Journal.sudo().search([
            ('code', '=', 'RDJ'),
            ('company_id', '=', user.company_id.id),
        ])
        if rounding_journal:
            return rounding_journal.sudo().write({
                'pos_method_type': 'rounding'
            })
        rounding_account_old_version = Account.sudo().search([
            ('code', '=', 'AAR'), ('company_id', '=', user.company_id.id)])
        if rounding_account_old_version:
            rounding_account = rounding_account_old_version[0]
        else:
            _logger.info('rounding_account have not')
            rounding_account = Account.sudo().create({
                'name': 'Rounding Account',
                'code': 'AAR',
                'user_type_id': self.env.ref('account.data_account_type_current_assets').id,
                'company_id': user.company_id.id,
                'note': 'code "AAR" give rounding pos order',
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'rounding_account' + str(user.company_id.id),
                'model': 'account.account',
                'module': 'pos_retail',
                'res_id': rounding_account.id,
                'noupdate': True,
            })
        rounding_journal = Journal.sudo().search([
            ('pos_method_type', '=', 'rounding'),
            ('company_id', '=', user.company_id.id),
        ])
        if rounding_journal:
            rounding_journal[0].sudo().write({
                'name': 'Rounding',
                'default_debit_account_id': rounding_account.id,
                'default_credit_account_id': rounding_account.id,
                'pos_method_type': 'rounding',
                'code': 'RDJ'
            })
            rounding_journal = rounding_journal[0]
        else:
            new_sequence = self.env['ir.sequence'].sudo().create({
                'name': 'rounding account ' + str(user.company_id.id),
                'padding': 3,
                'prefix': 'RA ' + str(user.company_id.id),
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'journal_sequence' + str(new_sequence.id),
                'model': 'ir.sequence',
                'module': 'pos_retail',
                'res_id': new_sequence.id,
                'noupdate': True,
            })
            rounding_journal = Journal.sudo().create({
                'name': 'Rounding',
                'code': 'RDJ',
                'type': 'cash',
                'pos_method_type': 'rounding',
                'journal_user': True,
                'sequence_id': new_sequence.id,
                'company_id': user.company_id.id,
                'default_debit_account_id': rounding_account.id,
                'default_credit_account_id': rounding_account.id,
                'sequence': 103,
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'rounding_journal_' + str(rounding_journal.id),
                'model': 'account.journal',
                'module': 'pos_retail',
                'res_id': int(rounding_journal.id),
                'noupdate': True,
            })

        config = self
        config.sudo().write({
            'journal_ids': [(4, rounding_journal.id)],
        })

        statement = [(0, 0, {
            'journal_id': rounding_journal.id,
            'user_id': user.id,
            'company_id': user.company_id.id
        })]
        current_session = config.current_session_id
        current_session.sudo().write({
            'statement_ids': statement,
        })
        return True

    @api.multi
    def open_ui(self):
        res = super(pos_config, self).open_ui()
        self.init_voucher_journal()
        self.init_wallet_journal()
        self.init_credit_journal()
        self.init_return_order_journal()
        self.init_rounding_journal()
        return res

    @api.multi
    def open_session_cb(self):
        res = super(pos_config, self).open_session_cb()
        self.init_voucher_journal()
        self.init_wallet_journal()
        self.init_credit_journal()
        self.init_return_order_journal()
        self.init_rounding_journal()
        return res
