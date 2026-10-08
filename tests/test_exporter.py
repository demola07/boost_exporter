import json
from decimal import Decimal
from typing import Any

from boost_exporter import DataExporter, ExportFormat


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