# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class RentRequest(models.Model):
    _name = 'rent.request'

    name = fields.Char(string="Number", readonly=True, required=True,
                       copy=False, default='New')
    customer_id = fields.Many2one('res.partner', string="Customer Name")
    request_date = fields.Date('Request Date', default=fields.Date.today)
    vehicle_id = fields.Many2one('vehicle.rental', string="Vehicle")
    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    period = fields.Char(string='Period')
    period_type = fields.Many2one('rent.charges', string='Period Type')
    unit = fields.Integer(string='Units',default=1)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda
                                      self: self.env.user.company_id.currency_id)
    rent_request = fields.Monetary(string='Rent', related="vehicle_id.rent")
    rent_total = fields.Monetary(string="Total Rent" ,compute='compute_rent',
                                 store=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm'),
         ('returned', 'Returned')], 'State', default='draft')

    @api.depends('unit')
    def compute_rent(self):
        self.write(
            {'rent_total': self.period_type.amount * self.unit})

    @api.onchange('from_date', 'to_date')
    def _onchange_get_period(self):
        for rec in self:
            if rec.from_date and rec.to_date:
                if rec.from_date < rec.to_date:
                    period_days = (rec.to_date - rec.from_date).days
                    rec.period = period_days + 1

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'vehicle.rental.sequence') or 'New'
        result = super(RentRequest, self).create(vals)
        return result

    @api.constrains('to_date', 'from_date')
    def date_check(self):
        for rec in self:
            if rec.to_date < rec.from_date:
                raise ValidationError(('Sorry Date Invalid'))

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'
            rec.vehicle_id.state = 'not_available'
            # rec.vehicle_id.request_ids = rec.vehicle_id

    def action_return(self):
        for rec in self:
            rec.state = 'returned'
            rec.vehicle_id.state = 'available'


class RequestCharges(models.Model):
    _name = 'rent.charges'
    _rec_name = 'time'

    vehicle_id = fields.Many2one('vehicle.rental', string="Vehicle")
    time = fields.Selection(
        [('hour', 'Hour'), ('day', 'Day'),
         ('week', 'Week'), ('month', 'Month')], 'Time', default='hour')

    amount = fields.Monetary(string='Amount')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda
                                    self: self.env.user.company_id.currency_id)
