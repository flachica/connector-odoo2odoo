# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
# Author: Fernando La Chica <greenice.com>

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)


class PaymentTermBatchImporter(Component):
    """Import the Odoo PaymentTerm."""

    _name = "odoo.account.payment.term.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.account.payment.term"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo Payment Term %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {"priority": 15}
            self._import_record(external_id, job_options=job_options)


class PaymentTermImportMapper(Component):
    _name = "odoo.account.payment.term.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.account.payment.term"]

    direct = [
        ("name", "name"),
        ("note", "note"),
    ]


class PaymentTermImporter(Component):
    _name = "odoo.account.payment.term.importer"
    _inherit = "odoo.importer"
    _apply_on = "odoo.account.payment.term"

    def _after_import(self, binding, force=False):
        binding.line_ids.unlink()
        if self.odoo_record.line_ids:
            _logger.info("Importing lines")
            for line_id in self.odoo_record.line_ids:
                self._import_dependency(
                    line_id.id, "odoo.account.payment.term.line", force=force
                )


class PaymentTermLineImporter(Component):
    _name = "odoo.account.payment.term.line.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.account.payment.term.line"]


class PaymentTermLineImportMapper(Component):
    _name = "odoo.account.payment.term.line.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.account.payment.term.line"]

    direct = [
        ("days", "days"),
    ]

    @mapping
    def payment_id(self, record):
        return {
            "payment_id": self.binder_for("odoo.account.payment.term")
            .to_internal(record.payment_id.id, unwrap=True)
            .id
        }

    @mapping
    def value(self, record):
        value = record.value
        if value == "procent":
            value = "percent"
        return {"value": value}

    @mapping
    def value_amount(self, record):
        if record.value == "procent":
            return {"value_amount": record.value_amount * 100}
        return {"value_amount": record.value_amount}
