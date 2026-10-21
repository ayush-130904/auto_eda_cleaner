<<<<<<< HEAD
# 📊 IntelliData AI

**An AI-powered data intelligence platform.** Upload a raw dataset and it profiles it, scores its quality, cleans it automatically (logging every decision), runs EDA, explains what it did with Gemini, assesses ML readiness, lets you chat with your data, and exports a PDF/HTML report.

> **Live demo:** _add your Render URL here_ · Click **"Load sample messy dataset"** on the home page to try it in one click.

<!-- Add 3-4 screenshots here: Quality page, Cleaning log, ML Readiness, Chat, PDF report -->

## What it does

| Stage | Feature |
|---|---|
| Ingest | CSV / Excel / JSON / Parquet upload with validation (type, size, empty-file checks) |
| Profile | Types, missing values, duplicates, constant & high-cardinality columns |
| Score | Completeness, duplicate, consistency, validity → one 0–100 quality score |
| Clean | Duplicates, whitespace/casing, missing values (median vs mean chosen *by outlier presence*), IQR outlier capping, final dedup pass. Every action is logged with method + reason |
| Analyze | Summary stats, skewness, correlations, interactive Plotly dashboard |
| AI layer (Gemini) | Cleaning explanations, executive summary, business insights, feature-engineering ideas, ML algorithm recommendations, dataset chatbot |
| ML readiness | Missing values, encoding, scaling, multicollinearity, class imbalance, target leakage → readiness score |
| Export | Downloadable PDF (ReportLab) and HTML (Jinja2) reports |

## Design decisions worth knowing

- **AI is an enhancement, never a single point of failure.** Every AI feature has a rule-based fallback (retry with exponential backoff first), so the app stays useful with no API key or during rate limits. The chatbot is the exception — open-ended Q&A has no honest fallback, so it reports the failure plainly.
- **The fallbacks are honest about their limits.** E.g. the business-insights fallback states what was *measured*, never invents a business story it can't back.
- **Logic is separated from UI.** `modules/` has zero Streamlit imports, so everything is unit-testable; `pages/` is thin rendering code.
- **Fail fast and cheap.** Upload validation checks extension and size before parsing.
- **Deliberately scoped:** single-user, in-session state, no auth/database — chosen to keep the app deployable on free tiers with no expiring services.

## Bugs the test suite caught (the interesting part)

- pandas 3.x uses a dedicated string dtype, so `dtype == object` silently skipped *every* text column during cleaning.
- A single mid-pipeline dedup isn't enough: string normalization **and** imputation can create new duplicates, so dedup runs again at the end.
- Target-leakage detection silently did nothing for categorical targets (the correlation matrix is numeric-only); fixed by correlating a binary target directly.
- The target column was being flagged as a feature needing encoding.

## Run locally

```bash
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add GEMINI_API_KEY (free key: aistudio.google.com/app/apikey)
streamlit run app.py
```

Tests: `pip install -r requirements-dev.txt && pytest` (118 tests; AI paths use an injected fake client — no network or key needed).

## Deploy (Render, free tier)

1. Push to GitHub. 2. Render → New → Blueprint → select the repo (`render.yaml` is picked up). 3. Set `GEMINI_API_KEY` in the dashboard. Free web services sleep after ~15 min idle, so the first load can take ~30–60s.

## Tech stack

Python 3.12 · Streamlit · pandas · NumPy · Plotly · statsmodels · google-genai (Gemini) · ReportLab · Jinja2 · pytest
=======
# IntelliData AI

An AI-powered data intelligence platform that automates dataset profiling,
quality assessment, intelligent cleaning, exploratory data analysis, and
generates AI-driven business insights and ML recommendations — with a
conversational chatbot for querying the dataset directly.

> Status: 🚧 Phase 1 — project scaffold. Feature pages land in later phases.

## Tech stack

Python · Streamlit · Pandas · scikit-learn · Plotly · Google Gemini API

## Local setup

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd IntelliData-AI

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# then edit .env and add your GEMINI_API_KEY

# 5. Run the app
streamlit run app.py
```
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced

## Project structure

```
<<<<<<< HEAD
app.py                 landing page
pages/                 10 Streamlit pages (Upload → … → Report)
modules/               loader, profiler, quality, cleaner, eda, visualizer, ml_readiness, report_generator
modules/ai/            client (retry), prompts, explainer, summary, insights, features, ml recs, chatbot
utils/                 config, logging, session state
templates/             Jinja2 report template
sample_data/           messy demo dataset
tests/                 pytest suite
```
=======
IntelliData-AI/
├── app.py              # Streamlit entry point
├── pages/              # feature pages (auto-discovered by Streamlit)
├── modules/             # data processing logic
│   └── ai/               # Gemini integration
├── utils/                # config, logging
├── uploads/ outputs/ reports/ logs/   # runtime data (git-ignored)
├── requirements.txt
├── .env.example
└── tests/
```

## Roadmap

- [x] Phase 1 — Project setup, config, logging
- [x] Phase 2 — Dataset upload & validation
- [x] Phase 3 — Data profiling
- [x] Phase 4 — Data quality scoring
- [x] Phase 5 — Intelligent cleaning engine
- [x] Phase 6 — Exploratory data analysis
- [x] Phase 7 — Visualization dashboard
- [x] Phase 8 — Gemini AI service layer
- [x] Phase 9 — AI cleaning explanations + executive summary
- [x] Phase 10 — AI business insights + feature engineering
- [x] Phase 11 — ML readiness + recommendation engine
- [x] Phase 12 — AI dataset chatbot
- [ ] Phase 13 — Report generation (PDF/HTML)
- [ ] Phase 14 — UI polish + Render deployment
- [ ] Phase 15 — Portfolio wrap-up
>>>>>>> 7fc5fc00838c5629a4b6e66db67a11bd58a73ced
