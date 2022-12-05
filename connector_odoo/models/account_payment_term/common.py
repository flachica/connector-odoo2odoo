# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Author: Fernando La Chica <greenice.com>


from odoo import fields, models

from odoo.addons.component.core import Component


class AccountPaymentTerm(models.Model):
    _name = "odoo.account.payment.term"
    _inherit = "odoo.binding"
    _inherits = {"account.payment.term": "odoo_id"}
    _description = "External Payment Term"

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    def resync(self):
        if self.backend_id.main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class PaymentTerm(models.Model):
    _inherit = "account.payment.term"

    bind_ids = fields.One2many(
        comodel_name="odoo.account.payment.term",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class AccountPaymentTermLine(models.Model):
    _name = "odoo.account.payment.term.line"
    _inherit = "odoo.binding"
    _inherits = {"account.payment.term.line": "odoo_id"}
    _description = "External Payment Term Line"

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    def resync(self):
        if self.backend_id.main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class PaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    bind_ids = fields.One2many(
        comodel_name="odoo.account.payment.term.line",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class PaymentTermAdapter(Component):
    _name = "odoo.account.payment.term.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.account.payment.term"
    _odoo_model = "account.payment.term"


class PaymentTermLineAdapter(Component):
    _name = "odoo.account.payment.term.line.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.account.payment.term.line"
    _odoo_model = "account.payment.term.line"
