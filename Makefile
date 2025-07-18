.PHONY: install lint test run

install:
	pip install -r requirements.txt

lint:
	flake8 src tests || true

test:
	pytest -q

run:
	streamlit run src/ui/app.py
