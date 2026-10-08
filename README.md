# Boost-exporter

A small Python module that exports datasets (a `list[dict]`) to **CSV** or **JSON**, with an in-memory cache that expires entries
after one hour.

📹 **[Watch the walkthrough video](https://drive.google.com/file/d/1LixNHLnsHWTZDLiPOmSkgayhMTwen2L0/view?usp=sharing)**: a short tour of the code, with a demo.

## Quick start

Requires [uv](https://docs.astral.sh/uv/). uv installs Python 3.12 from
`.python-version` if it isn't already available.

```bash
uv sync          # create .venv and install locked dependencies
uv run pytest    # run the test suite
```

For development, install the git hooks once:

```bash
uv run pre-commit install           # ruff check, ruff format and mypy --strict on every commit
uv run pre-commit run --all-files   # run the same checks by hand
```

## Try it with the sample dataset

`scripts/export_sample.py` exports the provided sample dataset from the
command line. The export goes to stdout, so you can redirect it to a file:

```bash
uv run python scripts/export_sample.py csv > sample.csv
uv run python scripts/export_sample.py json > sample.json
```

It also prints a one-line summary to stderr:

```
984 rows as csv: 4.2 ms, repeat from cache 1.3 ms
```

The script exports the same data twice in one run. The first export is a cache miss: it
serialises every row and stores the result. The repeat is a cache hit: it skips
serialisation and returns the stored export. The cache lives in memory for the life of
the process, so each run of the script starts with an empty cache.

## Usage

```python
import datetime

from boost_exporter import DataExporter, ExportError, ExportFormat

rows = [
    {"sku_name": "GEISHA 36× 180g box", "quantity": 17,
     "created_at": datetime.datetime(2023, 12, 5, 17, 18, 18)},
    {"sku_name": "KEY BAR ELEPHANT 16× 1,000g box", "quantity": 5,
     "created_at": datetime.datetime(2023, 12, 5, 17, 6, 22)},
]

exporter = DataExporter()                    # creates its own ExportCache
exporter.export(rows, ExportFormat.CSV)      # the enum...
exporter.export(rows, "json")                

try:
    exporter.export(rows, "xml")
except ExportError as exc:
    print(exc)  # Unsupported format 'xml'; expected one of: csv, json
```

CSV output:

```
sku_name,quantity,created_at
GEISHA 36× 180g box,17,2023-12-05T17:18:18
"KEY BAR ELEPHANT 16× 1,000g box",5,2023-12-05T17:06:22
```

JSON output:

```json
[{"sku_name": "GEISHA 36× 180g box", "quantity": 17, "created_at": "2023-12-05T17:18:18"}, {"sku_name": "KEY BAR ELEPHANT 16× 1,000g box", "quantity": 5, "created_at": "2023-12-05T17:06:22"}]
```

An empty dataset exports as `""` (CSV) or `"[]"` (JSON). To share a cache or change
its expiry, pass one in: `DataExporter(ExportCache(ttl=600))`.

## How it's built

- **Python 3.12**, packaged with **uv** (`pyproject.toml` + `uv.lock`).
- **attrs** for `ExportCache`
- **pytest** for tests, **ruff** for linting and formatting, **mypy** in strict mode
  for type checking, all run on every commit through **pre-commit**.

## Project layout

```
src/boost_exporter/
├── __init__.py    # public API: DataExporter, ExportCache, ExportError, ExportFormat
├── formats.py     # ExportFormat, encode_value, to_csv, to_json
├── exporter.py    # DataExporter, ExportError, validation, cache key
└── cache.py       # ExportCache (one-hour TTL)
scripts/
└── export_sample.py         # export the sample dataset from the command line
tests/
├── conftest.py              # sample_rows fixture (a fresh deep copy per test)
├── fixtures/sample_data.py  # the provided dataset
├── test_exporter.py
└── test_cache.py
```

## Testing

```bash
uv run pytest
```

The tests run against the provided sample dataset and small targeted inputs, covering:

- CSV and JSON output, checked by reading it back with `csv.DictReader` and `json.loads`
- rows with different columns
- invalid input (unsupported formats, malformed rows, values that can't be encoded)
- empty datasets
- cache expiry, using a fake clock so no test has to wait
- cache hits and misses through `DataExporter`
