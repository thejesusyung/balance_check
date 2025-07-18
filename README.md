# Balance Check

This repository contains utilities for reconciling Excel workbooks. It now
provides a Streamlit app for comparing two spreadsheets and highlighting any
imbalances between debit and credit values.

## Components
- `src/io/loader.py` – read Excel files into pandas DataFrames.
- `src/io/writer.py` – clone a workbook and highlight mismatches.
- `src/ui/app.py` – Streamlit UI for uploading files and running the
  reconciliation.

## Development
Install dependencies (requires `pandas`, `openpyxl`, etc.) and run tests with
`pytest`. Launch the web interface with:

```bash
streamlit run src/ui/app.py
```
