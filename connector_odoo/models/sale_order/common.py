# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component
from odoo.addons.component_event.components.event import skip_if

_logger = logging.getLogger(__name__)


class OdooSaleOrder(models.Model):
    _name = "odoo.sale.order"
    _inherit = "odoo.binding"
    _inherits = {"sale.order": "odoo_id"}
    _description = "External Odoo Sale Order"

    backend_amount_total = fields.Float()
    backend_amount_tax = fields.Float()
    backend_state = fields.Char()
    backend_picking_count = fields.Integer()
    backend_date_order = fields.Datetime()

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    # Can't seem to bind picking_ids in this model/method
    # Compute be will called in _set_state
    def _compute_import_state(self):
        for order_id in self:
            waiting = len(
                order_id.queue_job_ids.filtered(
                    lambda j: j.state in ("pending", "enqueued", "started")
                )
            )
            error = len(order_id.queue_job_ids.filtered(lambda j: j.state == "failed"))
            if waiting:
                order_id.import_state = "waiting"
            elif error:
                order_id.import_state = "error_sync"
            elif round(order_id.backend_amount_total, 2) != round(
                order_id.amount_total, 2
            ):
                order_id.import_state = "error_amount"
            elif order_id.backend_picking_count != len(order_id.picking_ids):
                order_id.import_state = "error_sync"
            else:
                order_id.import_state = "done"

    import_state = fields.Selection(
        [
            ("waiting", "Waiting"),
            ("error_sync", "Sync Error"),
            ("error_amount", "Amounts Error"),
            ("done", "Done"),
        ],
        default="waiting",
    )

    def name_get(self):
        result = []
        for op in self:
            name = "{} (Backend: {})".format(
                op.odoo_id.display_name, op.backend_id.display_name
            )
            result.append((op.id, name))

        return result

    def resync(self):
        if self.backend_id.read_operation_from == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )

    def _set_state(self):
        _logger.info("Setting state for %s", self)
        # All data was imported. Solve the state problem and all is done
        self._set_price_unit()
        self._set_sale_state()
        self._set_pickings_state()
        self._compute_import_state()

    def _set_price_unit(self):
        lines_without_price_unit = self.order_line.filtered(lambda l: not l.price_unit)
        if lines_without_price_unit:
            odoo_api = self.backend_id.get_connection().api
            order_line_model = odoo_api.get("sale.order.line")
            external_line_ids = order_line_model.search(
                [
                    ("order_id", "=", self.external_id),
                ]
            )
            # Iterate object only can be iterated once
            product_price_lines = []
            for line_id in external_line_ids:
                line_id = order_line_model.browse(line_id)
                product_id = (
                    self.env["odoo.product.product"]
                    .search([("external_id", "=", line_id.product_id.id)])
                    .odoo_id.id
                )
                if not product_id:
                    continue
                product_price_lines.append(
                    {"product_id": product_id, "price_unit": line_id.price_unit}
                )
        for line_id in lines_without_price_unit:
            for product_price_line in product_price_lines:
                product_id = product_price_line["product_id"]
                price_unit = product_price_line["price_unit"]
                if not price_unit:
                    continue
                if line_id.product_id.id == product_id:
                    line_id.price_unit = price_unit
                    break

    def _set_pickings_state(self):
        picking_ids = self.env["odoo.stock.picking"].search(
            [("sale_id", "=", self.odoo_id.id)], order="external_id"
        )
        for picking_id in picking_ids:
            picking_id._set_state()

    def _set_sale_state(self):
        if self.backend_state == self.odoo_id.state:
            return
        if self.backend_state in ("done", "progress") and self.odoo_id.state == "sale":
            return

        for line_id in self.odoo_id.order_line:
            line_id._compute_tax_id()
        self.odoo_id.onchange_partner_shipping_id()

        if self.backend_state == "waiting":
            self.odoo_id.action_confirm()
        elif self.backend_state == "confirmed":
            self.odoo_id.action_confirm()
        elif self.backend_state == "approved":
            self.odoo_id.action_confirm()
        elif self.backend_state in ("done", "progress"):
            self.odoo_id.action_confirm()
        elif "except" in self.backend_state:
            self.odoo_id.action_done()
        elif self.backend_state == "cancel":
            if not self.odoo_id.picking_ids.filtered(lambda x: x.state == "done"):
                self.odoo_id.action_cancel()
            else:
                self.odoo_id.action_done()
        self.date_order = self.backend_date_order
        # All pickings generated by Odoo must be deleted and imported from backend
        for picking_id in self.picking_ids:
            picking_id.unlink()


class SaleOrder(models.Model):
    _inherit = "sale.order"

    bind_ids = fields.One2many(
        comodel_name="odoo.sale.order",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )

    queue_job_ids = fields.Many2many(
        comodel_name="queue.job",
    )

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self._event("on_sale_order_confirm").notify(self)
        return res


class SaleOrderAdapter(Component):
    _name = "odoo.sale.order.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.sale.order"
    _odoo_model = "sale.order"


class SaleOrderListener(Component):
    _name = "odoo.sale.order.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["sale.order"]
    _usage = "event.listener"

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_sale_order_confirm(self, record):
        _logger.info("Not implemented yet. Ignoring on_sale_order_confirm  %s", record)


class OdooSaleOrderLine(models.Model):
    _name = "odoo.sale.order.line"
    _inherit = "odoo.binding"
    _inherits = {"sale.order.line": "odoo_id"}
    _description = "External Odoo Sale Order Line"

    def resync(self):
        if self.backend_id.main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    bind_ids = fields.One2many(
        comodel_name="odoo.sale.order.line",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class SaleOrderLineAdapter(Component):
    _name = "odoo.sale.order.line.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.sale.order.line"
    _odoo_model = "sale.order.line"
