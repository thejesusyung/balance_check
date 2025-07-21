# Balance Check

Balance Check is a small tool for reconciling debit and credit values between
any two Excel workbooks. It detects the relevant columns (optionally using the
OpenAI API), matches rows even across different layouts and highlights any
mismatches in copies of the original files. A simple Streamlit UI is provided
for interactive use.

## Installation

1. Clone this repository.
2. Install the dependencies:

```bash
make install  # or `pip install -r requirements.txt`
```

3. Create a `.env` file with your OpenAI API key (optional). You can copy the
   provided template:

```bash
cp .env.example .env
# then edit `.env` and set OPENAI_API_KEY=<your key>
```

The key is only required if you want the column detection to use the
OpenAI model. Without a key the heuristic fallback will be used.

## Usage

Run the Streamlit application:

```bash
make run  # or `streamlit run src/ui/app.py`
```

Upload the two workbooks, provide the API key if desired and press
**Reconcile**. The app first compares the total debit of the left workbook with
the total credit of the right. If they match a short confirmation is returned,
otherwise a detailed reconciliation is performed. In both cases the app offers
downloads for the coloured Excel files and a text report.

## Development

Lint the code, run the test-suite and start the UI via the provided Makefile:

```bash
make lint
make test
make run
```

The project structure follows:

- `src/io/loader.py` – Excel reading utilities.
- `src/io/writer.py` – write highlighted workbooks.
- `src/llm/` – OpenAI prompt and column detection logic.
- `src/core/` – reconciliation and highlighting algorithms.
- `src/ui/app.py` – Streamlit user interface.

