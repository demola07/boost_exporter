"""DataExporter: serialise a list-of-dict dataset to a chosen format."""

from collections.abc import Callable
from typing import Any

from boost_exporter.formats import ExportFormat, to_csv, to_json

type Rows = list[dict[str, Any]]

_SERIALISERS: dict[ExportFormat, Callable[[Rows], str]] = {
    ExportFormat.CSV: to_csv,
    ExportFormat.JSON: to_json,
}


class ExportError(Exception):
    """Raised when a dataset cannot be exported in the requested format."""


class DataExporter:
    """Exports datasets, as handed over by the database layer, to CSV or JSON."""

    def export(self, data: Rows, format: ExportFormat | str) -> str:
        """Serialise `data` to `format` and return the result as a string.

        `format` may be an ExportFormat or its string value, e.g. "csv".

        Raises:
            ExportError: if the format is unsupported, `data` is not a list of dicts,
                or a value cannot be encoded.
        """
        export_format = _parse_format(format)
        _validate(data)
        try:
            return _SERIALISERS[export_format](data)
        except (TypeError, ValueError) as exc:
            raise ExportError(f"Cannot export data as {export_format}: {exc}") from exc


def _parse_format(format: ExportFormat | str) -> ExportFormat:
    try:
        return ExportFormat(format)
    except ValueError:
        supported = ", ".join(ExportFormat)
        raise ExportError(
            f"Unsupported format {format!r}; expected one of: {supported}"
        ) from None


def _validate(data: object) -> None:
    """Check `data` is a list of dicts before any work is done on it."""
    if not isinstance(data, list):
        raise ExportError(f"Expected a list of dicts, got {type(data).__name__}")
    for index, row in enumerate(data):
        if not isinstance(row, dict):
            raise ExportError(f"Row {index} is {type(row).__name__}, not a dict")
