"""DataExporter: serialise a list-of-dict dataset to a chosen format."""

from collections.abc import Callable
from typing import Any

from boost_exporter.formats import ExportFormat, to_json

type Rows = list[dict[str, Any]]

_SERIALISERS: dict[ExportFormat, Callable[[Rows], str]] = {
    ExportFormat.JSON: to_json,
}


class DataExporter:
    """Exports datasets, as handed over by the database layer, to CSV or JSON."""

    def export(self, data: Rows, format: ExportFormat) -> str:
        """Serialise `data` to `format` and return the result as a string."""
        return _SERIALISERS[format](data)