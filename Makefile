check:
	python -m ruff check .
	python -m black --check .
	python -m pytest -q

