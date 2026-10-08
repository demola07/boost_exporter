"""DataExporter: serialise a list-of-dict dataset to a chosen format."""

import hashlib
import json
from collections.abc import Callable
from typing import Any

from boost_exporter.cache import ExportCache
from boost_exporter.formats import ExportFormat, encode_value, to_csv, to_json

type Rows = list[dict[str, Any]]

_SERIALISERS: dict[ExportFormat, Callable[[Rows], str]] = {
    ExportFormat.CSV: to_csv,
    ExportFormat.JSON: to_json,
}


class ExportError(Exception):
    """Raised when a dataset cannot be exported in the requested format."""


class DataExporter:
    """Exports datasets, as handed over by the database layer, to CSV or JSON.

    Exports are cached, so repeating an export of the same data in the same format
    within the cache's TTL returns the stored result instead of serialising again.
    """

    def __init__(self, cache: ExportCache | None = None) -> None:
        """Use `cache` if one is given, otherwise create a private one."""
        self.cache = cache if cache is not None else ExportCache()

    def export(self, data: Rows, format: ExportFormat | str) -> str:
        """Serialise `data` to `format` and return the result as a string.

        `format` may be an ExportFormat or its string value, e.g. "csv". An empty
        dataset exports as "" for CSV and "[]" for JSON.

        Raises:
            ExportError: if the format is unsupported, `data` is not a list of dicts,
                or a value cannot be encoded.
        """
        export_format = _parse_format(format)
        _validate(data)
        export_format = _parse_format(format)
        _validate(data)
        try:
            key = _cache_key(data, export_format)
            output = self.cache.get(key)
            if output is None:
                output = _SERIALISERS[export_format](data)
                self.cache.set(key, output)
        except (TypeError, ValueError) as exc:
            raise ExportError(f"Cannot export data as {export_format}: {exc}") from exc
        return output


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


def _cache_key(data: Rows, export_format: ExportFormat) -> str:
    """Key an export by its format and a SHA-256 hash of the data.

    Hashing the content rather than using `id(data)` means data changed after an
    export gets a new key, so a stale export is never served. Keys are not sorted:
    key order decides CSV column order, so the same values in a different order
    must not share an entry.
    """
    payload = json.dumps(data, default=encode_value)
    digest = hashlib.sha256(payload.encode()).hexdigest()
    return f"{export_format}:{digest}"
