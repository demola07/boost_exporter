import csv
import io
import json
from decimal import Decimal
from typing import Any
from unittest.mock import Mock

import pytest

from boost_exporter import DataExporter, ExportCache, ExportError, ExportFormat
from boost_exporter.exporter import _SERIALISERS


def test_json_export_round_trips_the_sample(sample_rows: list[dict[str, Any]]) -> None:
    output = DataExporter().export(sample_rows, ExportFormat.JSON)

    rows = json.loads(output)
    assert len(rows) == 984
    assert rows[0] == {
        "event_type": "Receive",
        "location_name": "Warehouse",
        "sku_name": "PEPSODENT CAVITY FIGHTER GH NEW 175g pack",
        "quantity": 111,
        "value": 53058,
        "created_at": "2023-12-05T17:04:16",
    }
    assert "KEY BAR ELEPHANT 16× 800g box" in output  # not escaped to \u00d7


def test_json_export_keeps_decimal_precision() -> None:
    output = DataExporter().export([{"amount": Decimal("1.10")}], ExportFormat.JSON)

    assert output == '[{"amount": "1.10"}]'


def test_csv_export_round_trips_the_sample(sample_rows: list[dict[str, Any]]) -> None:
    output = DataExporter().export(sample_rows, ExportFormat.CSV)

    rows = list(csv.DictReader(io.StringIO(output)))
    assert len(rows) == 984
    assert rows[0] == {
        "event_type": "Receive",
        "location_name": "Warehouse",
        "sku_name": "PEPSODENT CAVITY FIGHTER GH NEW 175g pack",
        "quantity": "111",
        "value": "53058",
        "created_at": "2023-12-05T17:04:16",
    }
    assert rows[2]["sku_name"] == "KEY BAR ELEPHANT 16× 1,000g box"  # comma survives


def test_csv_header_is_the_union_of_keys_across_rows() -> None:
    output = DataExporter().export([{"a": 1}, {"b": 2}], ExportFormat.CSV)

    assert output == "a,b\r\n1,\r\n,2\r\n"


def test_format_can_be_given_as_a_string(sample_rows: list[dict[str, Any]]) -> None:
    exporter = DataExporter()

    assert exporter.export(sample_rows, "csv") == exporter.export(
        sample_rows, ExportFormat.CSV
    )


@pytest.mark.parametrize(
    ("data", "export_format", "message"),
    [
        pytest.param([{"a": 1}], "xml", "Unsupported format", id="unknown-format"),
        pytest.param({"a": 1}, "json", "Expected a list", id="data-not-a-list"),
        pytest.param([{"a": 1}, 2], "json", "Row 1 is int", id="row-not-a-dict"),
        pytest.param([{"a": object()}], "csv", "type object", id="unencodable-csv"),
        pytest.param([{"a": object()}], "json", "type object", id="unencodable-json"),
        pytest.param([{"a": float("nan")}], "json", "JSON compliant", id="nan-json"),
    ],
)
def test_invalid_input_raises_export_error(
    data: Any, export_format: str, message: str
) -> None:
    with pytest.raises(ExportError, match=message):
        DataExporter().export(data, export_format)


@pytest.mark.parametrize(
    ("data", "export_format", "expected"),
    [
        pytest.param([], "csv", "", id="empty-csv"),
        pytest.param([], "json", "[]", id="empty-json"),
        pytest.param([{}], "csv", "", id="no-columns-csv"),
    ],
)
def test_empty_data_exports_without_error(
    data: list[dict[str, Any]], export_format: str, expected: str
) -> None:
    assert DataExporter().export(data, export_format) == expected


@pytest.fixture
def serialiser_spies(monkeypatch: pytest.MonkeyPatch) -> dict[ExportFormat, Mock]:
    """Wrap each serialiser in a Mock so tests can count real serialisations."""
    spies = {fmt: Mock(wraps=serialise) for fmt, serialise in _SERIALISERS.items()}
    for fmt, spy in spies.items():
        monkeypatch.setitem(_SERIALISERS, fmt, spy)
    return spies


def test_repeat_exports_are_served_from_the_cache(
    sample_rows: list[dict[str, Any]], serialiser_spies: dict[ExportFormat, Mock]
) -> None:
    exporter = DataExporter()

    for _ in range(2):
        exporter.export(sample_rows, "csv")
        exporter.export(sample_rows, "json")
        exporter.export([], "csv")  # "" is a cached export, not a miss

    assert serialiser_spies[ExportFormat.CSV].call_count == 2  # sample + empty
    assert serialiser_spies[ExportFormat.JSON].call_count == 1


def test_changed_data_is_not_served_from_the_cache(
    sample_rows: list[dict[str, Any]],
) -> None:
    exporter = DataExporter()
    before = exporter.export(sample_rows, "json")

    sample_rows[0]["quantity"] = 999

    assert exporter.export(sample_rows, "json") != before


def test_key_order_is_part_of_the_cache_key() -> None:
    exporter = DataExporter()

    assert exporter.export([{"a": 1, "b": 2}], "csv") == "a,b\r\n1,2\r\n"
    assert exporter.export([{"b": 2, "a": 1}], "csv") == "b,a\r\n2,1\r\n"


def test_uses_the_cache_it_is_given() -> None:
    cache = ExportCache()

    assert DataExporter(cache).cache is cache
