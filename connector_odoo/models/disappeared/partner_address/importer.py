# Copyright 2022 Greenice, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import logging

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class PartnerAddressDisappearedBatchImporter(Component):
    """Import the Odoo Partner from Address (OpenERP Model deprecated).

    For every partner address in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.res.partner.address.disappeared.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.res.partner.address.disappeared"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo partner address %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {"priority": 15}
            self._import_record(external_id, job_options=job_options, force=force)
