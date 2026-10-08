"""Export formats and the serialisers that produce them."""

import datetime
import json
from decimal import Decimal
from enum import StrEnum
from typing import Any

type Primitive = str | int | float | bool | None


class ExportFormat(StrEnum):
    """Formats that DataExporter can produce."""

    CSV = "csv"
    JSON = "json"


def encode_value(value: object) -> Primitive:
    """Convert a value from the database layer into a primitive every format can write.

    Dates and datetimes become ISO 8601 strings and Decimals become strings, so no
    precision is lost. Any other non-primitive type raises TypeError rather than being
    silently stringified.
    """
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, datetime.date):  # datetime.datetime is a subclass of date
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"Cannot export a value of type {type(value).__name__}")


def to_json(rows: list[dict[str, Any]]) -> str:
    """Serialise rows to a JSON array, keeping non-ASCII characters readable."""
    return json.dumps(rows, default=encode_value, ensure_ascii=False, allow_nan=False)