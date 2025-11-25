# Quick Run Guide

## 1. Build Vector Index (Chunking)

```bash
# Single ticker
python scripts/build_index.py --ticker AMZN --period Q3-2025

# Multiple tickers
python scripts/build_index.py --ticker AMZN --ticker MSFT --period Q3-2025
```

## 2. Start Backend API

```bash
uvicorn backend.app.main:app --reload
```
API runs at: `http://localhost:8000`

## 3. Start Streamlit Frontend

```bash
streamlit run frontend/streamlit_app.py
```
UI runs at: `http://localhost:8501`

## 4. Run Evaluation

```bash
# All models
python scripts/run_eval.py --csv data/eval/questions_example.csv --models all

# Specific models
python scripts/run_eval.py --csv data/eval/questions_example.csv --models claude-sonnet-4.5,gpt-5.1
```

**Note:** Backend must be running before evaluation.

