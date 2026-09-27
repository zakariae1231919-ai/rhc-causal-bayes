.PHONY: install lint test data demo
install: ; uv sync
lint:    ; uv run ruff check . && uv run ruff format --check .
test:    ; uv run pytest -q
data:    ; uv run python -m rhc_causal_bayes.data
demo:    ; uv run streamlit run app/app.py
