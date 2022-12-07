import logging

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)

_renames = {
    # "product.product,name": "product.template,name",
}


class DeliveryCarrierBatchImporter(Component):
    """Import the Odoo Translation."""

    _name = "odoo.delivery.carrier.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.delivery.carrier"]


class DeliveryCarrierImportMapper(Component):
    _name = "odoo.delivery.carrier.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.delivery.carrier"]

    direct = [("name", "name")]


class DeliveryCarrierImporter(Component):
    _name = "odoo.delivery.carrier.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.delivery.carrier"]
