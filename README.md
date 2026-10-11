# StatGenius AI - AI-Powered Statistical Learning Assistant (hackathon prototype)

Helps learners in India's Official Statistical System find competency gaps, study from their own PDFs, practise with generated quizzes,
understand mistakes, and follow a rule-based learning path. **Works fully without any paid API key (demo mode).**

## Features
Competency assessment (27 verified questions, 9 topics, confidence ratings) - gap detection (configurable thresholds, radar chart, comparison with previous
assessment) - PDF -> notes and quizzes with page references (MCQ, true/false, short answer, numerical) - Explain My Mistake with similar practice question -
adaptive learning path (documented rules in `backend/learning_engine.py`) - Practice Lab (7 validated calculators with steps) - AI Tutor (demo library or LLM) -
dashboard (all values derived from the database) - **sample** iGOT course mapping (`backend/igot_demo.py`, clearly labelled, NOT connected to iGOT Karmayogi).

## Stack
HTML/CSS/vanilla JS + Chart.js (CDN) - FastAPI - SQLite + SQLAlchemy - PyMuPDF - optional Anthropic API (server side only).
Layout is simplified from the brief: one single-page frontend (`frontend/index.html`, hash-routed views in `frontend/js/`).

## Setup (VS Code)
Prerequisites: Python 3.10+ and internet access for `pip` and the Chart.js CDN.
```bash
cd statgenius-ai
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env            # Windows: copy .env.example .env   (set SECRET_KEY; API key optional)
cd backend
python init_db.py               # creates SQLite DB, question bank and the sample demo learner
uvicorn main:app --reload --port 8000
```
Open **http://localhost:8000** - the backend also serves the frontend. API docs: **http://localhost:8000/docs**.
(Alternative: serve `frontend/` with VS Code Live Server on port 5500; the frontend then calls the API at localhost:8000, which CORS already allows.)

## Demo script (no API key needed)
1. "Start Learning" -> Demo mode (sample data) -> Dashboard. 2. Assessment -> answer -> Submit (real scores, weak topics, radar).
3. PDF Learning -> "Use sample PDF" (or upload your own text PDF) -> Generate notes -> Generate quiz (try Mixed).
4. Submit quiz -> "Explain my mistake" on a wrong answer -> try the similar question. 5. Learning Path: progress, next step, sample iGOT courses -> Track.
6. Dashboard again: updated scores, activities, streak. 7. AI Tutor suggested questions.
Real AI: put `ANTHROPIC_API_KEY` in `.env` and restart; notes summaries, mistake explanations and the tutor then use the LLM (answer keys are still validated/computed in code).

## Tests
`pip install pytest` then `pytest tests` from the project root (covers grading, competency, learning rules, quiz validation, statistics).

## Honest limitations
* Written and unit-tested in an environment **without network access**: the pure-logic modules (grading, competency, learning engine, quiz generator, stats lab) were run and tested;
  **the FastAPI server, SQLAlchemy models, PyMuPDF extraction and browser UI could not be executed there** (only syntax-checked). Expect to fix small integration issues on first run - please report tracebacks.
* Quiz generation in demo mode is rule-based (cloze/true-false from definition sentences); quality depends on the PDF. Scanned PDFs are rejected (OCR not implemented).
* Scores are short-quiz indicators, not measures of professional competency; AI text is clearly separated from computed results.
* iGOT Karmayogi is simulated with sample records; no official integration exists. Auth is prototype-grade (PBKDF2 hashing, signed tokens, no email verification/rate limiting).
* Frontend is one page rather than the five HTML files in the brief; cluster/other advanced topics in the lab are limited to the seven calculators.

## Troubleshooting
`ModuleNotFoundError` -> activate the venv and reinstall requirements. Port busy -> use `--port 8001` (frontend auto-detects only 8000; edit `API` in `frontend/js/app.js`).
"Cannot reach the server" -> start uvicorn. PDF rejected -> must be a text PDF under 5 MB. Charts missing -> Chart.js CDN needs internet.
Sessions reset after restart -> set `SECRET_KEY` in `.env`.
