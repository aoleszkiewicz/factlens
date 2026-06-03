# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Bachelor thesis (SSN — sieci neuronowe). Binary fake-news classifier on the Kaggle *Fake and Real News Dataset* (`clmentbisaillon/fake-and-real-news-dataset`). Target architecture: **BiLSTM + Attention** with **GloVe 300d** embeddings, implemented in **strict PyTorch** (no TF/Keras/JAX, no HuggingFace `Trainer`, no Lightning). Full project brief: `docs/project_description_ssn.md`.

The `src/api/`, `src/frontend/` packages are scaffolds — currently empty. Real code lives in `notebooks/`, `src/data/` (cleaning, splits, GloVe OOV analysis) and `src/model/` (TF-IDF + LogReg baseline). The BiLSTM + Attention model is not implemented yet (`torch` is not a dependency).

## Conventions

- **Label**: `1 = Real`, `0 = Fake`.
- **File format**: one consistent format for intermediate data — **CSV** everywhere (readable diffs, simplicity, acceptable size for this dataset). Do not reintroduce Parquet; cleaning output, splits, and the baseline all read/write CSV only.
- **Model input**: only the `text` column. `title`, `subject`, `date` are dropped — `subject` is rozłączny per klasa (czysty leakage), all Fake `date`s use a non-default format, `title` correlates stylistically with class.
- **Language**: code, identifiers, commit messages → **English**. Notebook markdown / wnioski / plot titles / report prose → **Polish** (thesis language).
- **Plotting**: `pd.options.plotting.backend = "plotly"` + `plotly.express`. seaborn was used in `*_temp/` archives; new code is plotly-first.
- **Notebook hygiene**: each analytical block ends with a markdown cell starting `**Wniosek (N).**`. Keep individual notebooks focused — split rather than balloon.

## Repository layout

```
data/raw/         True.csv, Fake.csv  (downloaded via kagglehub at runtime)
data/processed/   news_cleaned.csv, news_classification_profile_report.html
data/processed/splited/   train.csv, val.csv, test.csv  (written by make_splits)
docs/             project brief (Polish)
notebooks/explore/      current EDA + cleaning notebooks
notebooks/explore_temp/ archive — read-only, do not modify
notebooks/report/       thesis-facing report notebooks
notebooks/report_temp/  archive — read-only, do not modify
src/data/cleaning.py   regex-based artifact stripping + length filter
src/data/splits.py     stratified train/val/test split helper
src/data/glove.py      GloVe vocab loading + OOV coverage report
src/model/baseline.py  TF-IDF + Logistic Regression baseline (build/evaluate/top_features)
```

The `*_temp/` directories are intentional historical archive from a prior iteration — keep as reference, never edit. Current work lives in `notebooks/explore/` and `notebooks/report/`.

## Pipeline flow

1. `notebooks/explore/01_eda.ipynb` — EDA on raw `True.csv`/`Fake.csv` (kagglehub download). Establishes: balance ~52/48 (Fake/Real), ~14% duplicates (almost all Fake), 95th percentile ≈ 900 słów (candidate `max_seq_len`), and the leakage signals to investigate.
2. `notebooks/explore/02_leakage.ipynb` — chi² / MI on Reuters dateline, URL/handle markers; TF-IDF top n-grams per class; produces the regex list that feeds `src/data/cleaning.py`.
3. `notebooks/explore/03_cleaning.ipynb` — applies `clean_text` + `filter_short_articles` based on the markers identified upstream; writes `data/processed/news_cleaned.csv`.
4. `notebooks/explore/04_post_cleaning.ipynb` — sanity check that markers from `02_leakage` are gone, re-runs key stats on the cleaned CSV, optional GloVe coverage check.
5. `notebooks/explore/05_splits.ipynb` — calls `make_splits` (from `src.data.splits`) to write stratified `train.csv`/`val.csv`/`test.csv`.
6. `notebooks/report/00_raport.ipynb` — final consolidated thesis-facing report; gathers all wnioski and decisions.
7. `notebooks/report/02_baseline_tfidf_lr.ipynb` — TF-IDF + Logistic Regression baseline: metrics on val/test, confusion matrix, ROC, plus LR-coefficient explainability (uses `src.model.baseline`).

`src/data/cleaning.py` exposes:
- `clean_text(text: str) -> str` — strips Reuters wire markers, dateline prefixes, URLs, `@handles`, photo-credit templates, HTML, site-specific signatures (`21st Century Wire`), single-letter tokens, then lowercases. Order matters; the upstream EDA in `notebooks/explore_temp/03_leakage_analysis.ipynb` justifies each pattern.
- `filter_short_articles(df, min_words=10)` — drops rows after cleaning.

## Type annotations

Pyright is configured in `pyproject.toml` (`[tool.pyright]`, `typeCheckingMode = "basic"`). Pylance in VS Code reads this automatically — hover types and completions are driven by annotations in `src/`.

**Rules:**
- Annotate every function parameter and return type. No bare `def f(x)` — always `def f(x: T) -> R`.
- Use Python 3.12+ built-in generics everywhere. Never import `List`, `Dict`, `Tuple`, `Optional` from `typing` — use `list[str]`, `dict[str, int]`, `tuple[int, ...]`, `X | None` instead.
- `from __future__ import annotations` is not needed on Python 3.12+; do not add it.
- For pandas: use `pd.DataFrame` and `pd.Series` as types (no subscript needed — stubs don't support it).
- For `Path`: import from `pathlib`, not `os.path`.
- Module-level constants don't need explicit annotations when the type is obvious from the literal (`RANDOM_STATE = 42` is fine), but annotate when the inferred type would be too broad.

**Reference implementations** (already fully typed):
- `src/data/cleaning.py` — `clean_text(text: str) -> str`, `filter_short_articles(df: pd.DataFrame, min_words: int) -> pd.DataFrame`
- `src/data/splits.py` — `make_splits(df: pd.DataFrame, output_dir: Path, write_to_file: bool, random_state: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]`
- `src/data/glove.py` — `load_glove_vocab(path: Path) -> set[str]`, `oov_report(texts: pd.Series, glove_vocab: set[str], top_n: int) -> dict[str, object]`
- `src/model/baseline.py` — `build_baseline(...) -> Pipeline`, `evaluate(...) -> dict[str, object]`, `top_features(...) -> tuple[list, list]`

## Commands

Dependency manager is `uv` (Python 3.12+, see `.python-version`). Use `uv` directly, not `pip` — the venv has no `pip` installed.

```bash
uv sync                                     # install/update dependencies from uv.lock
uv lock                                     # regenerate lockfile after pyproject.toml changes
uv add <pkg>                                # add a runtime dep
uv add --dev <pkg>                          # add a dev dep
uv run python main.py                       # run the (currently stub) entrypoint
uv run jupyter lab                          # start Jupyter against the project venv

# Execute a notebook end-to-end (smoke test):
uv run jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=600 notebooks/explore/01_eda.ipynb
```

If `uv run` fails with `Failed to parse uv.lock`, regenerate with `mv uv.lock uv.lock.bak && uv lock && uv sync`.

No tests, linters, or formatters are configured yet (`tests/__init__.py` is empty; no `ruff`/`black`/`pytest` in `pyproject.toml`).

## External assets

- **Kaggle dataset** is fetched at notebook runtime via `kagglehub.dataset_download("clmentbisaillon/fake-and-real-news-dataset")` — no manual download needed, but kagglehub credentials must be set up.
- **GloVe 6B 300d** is *not* in the repo. Notebooks expect `data/glove/glove_2024_wikigiga_300d`

## When working here

- Notebook prose, plot titles, and wnioski must be in Polish; code stays English.
- Don't pull in HF `tokenizers`/`transformers` for tokenization — model side will use plain Python regex/whitespace tokenization + GloVe lookup, owned in PyTorch.
- Don't touch `notebooks/*_temp/` — those are frozen reference.
- When editing notebooks, use `NotebookEdit` (insert/replace/delete cells by id). Do not generate Python scripts to manipulate `.ipynb` files. Use `nbconvert --execute --inplace` only as a smoke test / end-to-end run.

## Claude Code setup

Preferred mode is **VS Code extension panel**. Available tools in this mode:
- `NotebookEdit` — add/edit/delete notebook cells (primary tool for notebook work)
- `Read` — inspect notebook cells and outputs
- `Bash(uv run *)` — run scripts, nbconvert smoke tests, uv commands
- `mcp__ide__executeCode` / `mcp__ide__getDiagnostics` — only available in integrated terminal mode, not panel; do not rely on them

VS Code workspace settings are in `.vscode/settings.json` (default uv interpreter, Pylance basic mode).
