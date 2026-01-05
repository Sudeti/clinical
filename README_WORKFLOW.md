# Clinical Sovereign — End-to-End Workflow (A → Z) ✅

This README explains the full workflow from draft submission through multi-LLM evaluation, structured parsing, consensus logic, UI presentation, and database considerations.

---

## 1) Overview 💡

High-level flow:
- User submits a draft to the evaluation UI (`/evaluate`).
- Backend creates a `DraftCritique` record in a `PROCESSING` state.
- A Celery task (`run_full_critique_task`) invokes `SovereignCriticEngine` to call three LLMs.
- Each LLM is asked to return a strict JSON object (machine-readable schema).
- Raw LLM outputs are saved, then `CritiqueAnalyzer` parses JSON, applies venom-vs-value logic, and produces a consensus.
- The database record is updated with structured fields (scores, artifact, forbidden alternatives, sentence triggers, historical correlation).
- User refreshes the page and sees metrics, flagged sentences, sovereign alternatives, and the suggested artifact.

---

## 2) Key modules 🔧

- `critique/llm_evaluators.py` — Builds prompt (now enforces JSON output), calls Claude/GPT/Gemini, returns raw text.
- `critique/analyzers.py` — Parses JSON responses, CSV fallback, computes consensus using venom vs value rules.
- `critique/tasks.py` — Celery task (`run_full_critique_task`) that orchestrates LLM calls and persists structured results.
- `critique/models.py` — `DraftCritique`, `ArchivedPost`, `PersonaBio`, `CommentGeneration` (indexes and JSON fields added).
- `critique/views.py` & `critique/templates/evaluate.html` — UI: highlighted sentences and Forbidden Alternatives table.

---

## 3) Required environment & services ⚙️

Environment variables (required):
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- Standard Django DB settings

Recommended: run a Celery worker and a broker (Redis), monitor LLM usage/costs.

---

## 4) LLM JSON Schema (strict) 🧾

The LLM must return a single JSON object (no extra text) with these keys and types:

```json
{
  "physics_engine_score": 0,           // int 0-100
  "zero_kelvin_shield_score": 0,      // int 0-100
  "verdict_output_score": 0,          // int 0-100
  "scalpel_edge_score": 0,            // int 0-100
  "kinetic_action_score": 0,          // int 0-100
  "clinical_tone_score": 0,           // int 0-100 weighted avg
  "venom_density": 0,                 // int 0-100
  "value_density": 0,                 // int 0-100
  "structural_failures": [],          // array of strings
  "artifact": "",                   // string (2x2 matrix, checklist, etc.)
  "forbidden_alternatives": {         // object mapping forbidden -> [alts]
     "excited": ["pleased", "notable"]
  },
  "sentence_triggers": [0, 2],        // indexes (0-based) of sentences to highlight
  "final_verdict": "CLEAR",         // string: CLEAR/REVISE/REJECT
  "notes": "Optional short explanation"
}
```

Example outputs are included in unit tests under `critique/tests/`.

> Note: The analyzer will try to extract JSON blocks if the LLM returns additional text, but best practice is to ensure the LLM returns a clean JSON object.

---

## 5) Database & migrations 🗃️

Changes made:
- Added `historical_avg_clinical_score` (DecimalField) to `DraftCritique`.
- Added `artifact` (TextField), `forbidden_alternatives` (JSONField), `sentence_triggers` (JSONField) to `DraftCritique`.
- Added indexes on `DraftCritique(user, submitted_at)`, `DraftCritique(submitted_at)` and `CommentGeneration(user, created_at)`.
- Added `PROCESSING` to `consensus_verdict` choices to allow creation before task completion.

Migration steps:

```bash
python manage.py makemigrations critique
python manage.py migrate
```

Caveats:
- `JSONField` requires Django >= 3.1 (native) — verify your Django version.
- If you need to backfill `historical_avg_clinical_score`, write a data migration or a management command to re-run scoring for historical posts.

---

## 6) Running the system locally 🏃‍♂️

Install requirements, set env vars, then:

```bash
# optional create virtual env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# create DB and run migrations
python manage.py migrate

# run Django server
python manage.py runserver

# run Celery worker (assuming Redis broker)
celery -A config worker -l info
```

Submit a draft in the UI, then either watch the worker or refresh `/evaluate` after ~30s to see results.

---

## 7) Tasks, retries & historical scoring ⏱️

- `run_full_critique_task` is configured with `max_retries=2` and `retry` behavior to handle transient API errors.
- Historical correlation: For performance reasons, we evaluate top N (default 3) archived posts to compute `historical_avg_clinical_score`. This increases LLM calls; consider periodic precomputation if cost is a concern.

---

## 8) UI behavior & highlighting 🩺

- The template displays the most recent `DraftCritique` as `current_critique`.
- `sentence_triggers` contains 0-based indexes of sentences that caused REJECT/REVISE and are highlighted via `<mark>` in `evaluate.html`.
- `forbidden_alternatives` renders as a table mapping forbidden term -> alternatives.
- The `artifact` is shown in a separate box (the "Third Object").

Implementation note: sentence splitting uses a lightweight regex: `(?<=[.!?])\s+` — tune if your input includes non-standard punctuation.

---

## 9) Testing & validation 🧪

- Add tests for:
  - Valid LLM JSON parsing
  - Malformed / partial JSON fallback
  - Venom vs value scenarios (ensure consensus rules produce the expected verdict)
  - `sentence_triggers` highlighting logic
- Run tests:

```bash
python manage.py test critique
# or with pytest (optional)
pip install pytest
pytest -q
```

Mocks:
- Mock LLM API clients in unit tests to ensure deterministic behavior and to avoid API costs during CI.

---

## 10) Observability & debugging 🔎

- Raw LLM outputs are persisted in `DraftCritique` fields: `claude_critique`, `gpt_critique`, `gemini_critique`.
- If parsing fails, check these fields and run `python manage.py shell` to inspect or re-run the `run_full_critique_task` for a record.

Tip: Add logging around LLM calls and JSON parsing to easily surface malformed outputs.

---

## 11) Costs & safety considerations 💸🔐

- Each evaluation hits 3 LLMs; historical scoring adds N extra calls (top posts). Watch for cost. Options:
  - Limit historical scoring or run it in a scheduled job.
  - Use a cached value per archived post.
- Keep API keys in environment; avoid committing them.

---

## 12) Future improvements ✨

- Add JSON Schema validation for LLM outputs and reject invalid responses early.
- Add precomputation or caching of historical scores to reduce per-submission cost.
- Provide an admin UI for re-evaluating specific `DraftCritique` records.
- Optional: accept multiple LLM strategies and weight them dynamically.

---

## 13) Troubleshooting checklist ⚠️

- If you see `avg_clinical_score = N/A` or `consensus_verdict == PROCESSING` after long wait:
  1. Check Celery worker status and logs.
  2. Inspect `DraftCritique.claude_critique` (and gpt/gemini) for raw outputs.
  3. Ensure API keys are valid and not rate-limited.

---

## 14) Contributing / Making changes 🙌

- Fork, implement, add tests for new behavior, and open a PR.
- For data-model changes, include migrations and document back-fill steps.

---

If you'd like, I can:
- Add a JSON Schema validator for responses and a test suite for malformed JSON
- Create a management command to backfill `historical_avg_clinical_score`
- Add an opt-out flag to the model to skip historical scoring per-request

---

_Last updated: Jan 2026_
