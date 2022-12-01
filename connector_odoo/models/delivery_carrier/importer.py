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

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo Carrier %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {"priority": 15}
            self._import_record(external_id, job_options=job_options, force=force)


class DeliveryCarrierImportMapper(Component):
    _name = "odoo.delivery.carrier.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.delivery.carrier"]

    direct = [("name", "name")]


class DeliveryCarrierImporter(Component):
    _name = "odoo.delivery.carrier.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.delivery.carrier"]
