NAME = fly-in

PYTHON = uv run python
FILE ?= maps/easy/01_linear_path.txt

install:
	uv sync

run:
	$(PYTHON) -m src $(FILE)

debug:
	$(PYTHON) -m pdb src/__main__.py $(FILE)

visual:
	$(PYTHON) -m src $(FILE) --visual

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

lint:
	uv run flake8 . --exclude=.venv,__pycache__,.mypy_cache
	uv run mypy . --exclude '\.venv' \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs


.PHONY: install run debug visual clean lint