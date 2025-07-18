# Balance Check

This repository contains utilities for reconciling Excel workbooks. The current focus is on input/output helpers used by the reconciliation pipeline.

## Components
- `src/io/loader.py` – read Excel files into pandas DataFrames.
- `src/io/writer.py` – clone a workbook and highlight mismatches.

## Development
Install dependencies (requires `pandas`, `openpyxl`, etc.) and run tests with `pytest`.
