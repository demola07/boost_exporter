"""Export the provided sample dataset to CSV or JSON.

Usage:
    uv run python scripts/export_sample.py csv > sample.csv
    uv run python scripts/export_sample.py json > sample.json
"""

import argparse
import runpy
import sys
import time
from pathlib import Path

from boost_exporter import DataExporter, ExportFormat

SAMPLE_DATA = Path(__file__).parents[1] / "tests" / "fixtures" / "sample_data.py"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the sample dataset.")
    parser.add_argument("format", choices=[str(fmt) for fmt in ExportFormat])
    args = parser.parse_args()

    rows = runpy.run_path(str(SAMPLE_DATA))["data"]
    exporter = DataExporter()

    started = time.perf_counter()
    output = exporter.export(rows, args.format)
    first_ms = (time.perf_counter() - started) * 1000

    started = time.perf_counter()
    exporter.export(rows, args.format)
    cached_ms = (time.perf_counter() - started) * 1000

    sys.stdout.write(output)
    sys.stderr.write(
        f"{len(rows)} rows as {args.format}: {first_ms:.1f} ms, "
        f"repeat from cache {cached_ms:.1f} ms\n"
    )


if __name__ == "__main__":
    main()
