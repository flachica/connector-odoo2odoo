import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooDeliveryCarrier(models.Model):
    _name = "odoo.delivery.carrier"
    _inherit = "odoo.binding"
    _inherits = {"delivery.carrier": "odoo_id"}
    _description = "External Odoo Carrier"

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


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    bind_ids = fields.One2many(
        comodel_name="odoo.delivery.carrier",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class DeliveryCarrierAdapter(Component):
    _name = "odoo.delivery.carrier.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.delivery.carrier"

    _odoo_model = "delivery.carrier"


class DeliveryCarrierListener(Component):
    _name = "delivery.carrier.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["delivery.carrier"]
    _usage = "event.listener"
