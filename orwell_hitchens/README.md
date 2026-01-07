# Orwell-Hitchens Writing Engine

A multi-LLM evaluation system that critiques writing using principles from George Orwell's "Politics and the English Language" and Christopher Hitchens's rhetorical mastery.

## Philosophy

This engine combines:

1. **Orwellian Clarity (40% weight)**: Concrete over abstract, active voice, sentence variety, jargon-free
2. **Hitchensian Fire (30% weight)**: Argument structure, logical scaffolding, rhetorical devices, wit, intellectual honesty
3. **Vivid Physicality (20% weight)**: Sensory language, metaphor coherence, concrete imagery
4. **Technical Execution (10% weight)**: Grammar, redundancies, clichés, flow

## Architecture

### Core Components

```
orwell_hitchens/
├── models.py              # WriterProfile, PublishedPiece, DraftEvaluation, SuggestedRevision
├── llm_evaluators.py      # OrwellHitchensEngine (Claude, GPT, Gemini)
├── analyzers.py           # WritingAnalyzer (consensus, scoring, highlighting)
├── tasks.py               # Celery task for async evaluation
├── views.py               # Django views (evaluate, detail, history)
├── urls.py                # URL routing
├── admin.py               # Django admin configuration
└── templates/
    └── orwell_hitchens/
        ├── evaluate.html  # Main evaluation interface
        ├── detail.html    # Detailed evaluation view
        └── history.html   # Past evaluations archive
```

### Multi-LLM Evaluation

The engine queries three LLMs in parallel:
- **Claude Sonnet 4**: Strong on rhetorical analysis
- **GPT-4o**: Structured JSON outputs
- **Gemini 2.0 Flash**: Fast, diverse perspectives

Consensus is calculated by averaging scores and combining insights.

## Setup

### 1. Add to Django Settings

Already configured in `config/settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'orwell_hitchens',
]
```

### 2. Configure Environment Variables

Ensure these are set in your `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
```

### 3. Run Migrations

```bash
python manage.py migrate orwell_hitchens
```

### 4. Create Writer Profile

In Django admin (`/admin/orwell_hitchens/writerprofile/`), create a `WriterProfile` for your user:

- **Professional Context**: e.g., "Foreign Policy Analyst"
- **Writing Domains**: Your areas of expertise
- **Style Preferences**: Your writing principles
- **Target Publications**: e.g., "The Atlantic, Foreign Affairs"
- **Forbidden Jargon**: Comma-separated list (e.g., "synergy, leverage, robust")

### 5. Add Published Pieces (Optional but Recommended)

In Django admin (`/admin/orwell_hitchens/publishedpiece/`), add your best published work. The engine uses this to:
- Calibrate to your personal style
- Compare current drafts to your historical performance
- Provide context to LLMs

## Usage

### Web Interface

1. Navigate to `/orwell/`
2. Paste your draft (minimum 100 characters)
3. Click "EXECUTE EVALUATION"
4. Wait 30-60 seconds for async processing
5. Review detailed results:
   - **Overall Score**: Weighted average (40% Clarity, 30% Fire, 20% Physicality, 10% Technical)
   - **Verdict**: PUBLISH / REVISE / REWRITE
   - **Structural Analysis**: Abstract nouns, passive voice, jargon, weak verbs
   - **Rhetorical Highlights**: Strengths detected
   - **Raw LLM Critiques**: Full analysis from each model

### Interpreting Results

#### Scores (0-100)

- **85-100**: Excellent. Ready for top-tier publication.
- **70-84**: Strong. Minor refinements recommended.
- **55-69**: Adequate. Significant revision needed.
- **Below 55**: Weak. Structural rewrite required.

#### Verdicts

- **PUBLISH**: All systems nominal. Content meets Orwell-Hitchens standards.
- **REVISE**: Good foundation but needs refinement.
- **REWRITE**: Structural failures detected. Fundamental rewrite needed.

#### Flagged Issues

The engine highlights specific problems:

1. **Abstract Nouns**: Words like "situation," "aspect," "factor," "context"
   - **Fix**: Replace with concrete, specific language
   
2. **Passive Voice**: Sentences highlighted in yellow
   - **Fix**: Use active voice. "The policy was implemented" → "Diplomats implemented the policy"
   
3. **Jargon/Euphemisms**: Bureaucratic language with suggested alternatives
   - **Fix**: Use plain, direct language
   
4. **Weak Verbs**: "is," "has," "seems," "appears"
   - **Fix**: Use action verbs that show rather than tell

## Evaluation Criteria (Detail)

### I. Orwellian Clarity (40%)

**Assessed Metrics:**
- Concrete/Abstract ratio (penalize abstract nouns)
- Active/Passive voice ratio (active preferred)
- Sentence length variance (mix short and long)
- Jargon density (flag bureaucratic euphemisms)
- Word choice (Anglo-Saxon over Latinate)

**Orwell's Rules:**
1. Never use a long word where a short one will do
2. If it is possible to cut a word out, always cut it out
3. Never use the passive where you can use the active
4. Never use a foreign phrase, scientific word, or jargon if you can think of an everyday English equivalent

### II. Hitchensian Fire (30%)

**Assessed Metrics:**
- Argument density (claims per paragraph)
- Logical coherence (premises → conclusions)
- Rhetorical devices:
  - Parallelism (repeating structure)
  - Antithesis (contrasting ideas)
  - Tricolon (three-part lists)
- Wit quality (unexpected comparisons, precision insults)
- Intellectual honesty (addresses counterarguments?)

**Hitchens's Rule:**
"What can be asserted without evidence can be dismissed without evidence."

### III. Vivid Physicality (20%)

**Assessed Metrics:**
- Sensory language percentage (sight, sound, touch, smell, taste)
- Metaphor coherence (deductions for mixed metaphors)
- Concrete imagery vs. vague generalities
- "Show don't tell" ratio

**Combined Rule:**
Make abstractions visible, tangible, smellable.

### IV. Technical Execution (10%)

**Assessed Metrics:**
- Grammar correctness
- Redundancy count ("very," "really," "actually," "basically")
- Cliché count (tired phrases)
- Flow quality (transitions, logical gaps)

## API / Programmatic Usage

```python
from orwell_hitchens.llm_evaluators import OrwellHitchensEngine
from orwell_hitchens.analyzers import WritingAnalyzer
from orwell_hitchens.models import WriterProfile, PublishedPiece

# Get profile and calibration data
profile = WriterProfile.objects.get(user=user)
published_pieces = PublishedPiece.objects.filter(user=user)[:5]

# Initialize engine
engine = OrwellHitchensEngine(profile, published_pieces)

# Evaluate draft
draft_text = "Your writing here..."
critiques = engine.execute_full_evaluation(draft_text)

# Calculate consensus
consensus = WritingAnalyzer.calculate_consensus(critiques)

print(f"Overall Score: {consensus['overall_score']}")
print(f"Verdict: {consensus['consensus_verdict']}")
print(f"Abstract Nouns: {consensus['abstract_nouns']}")
```

## Celery Integration

Evaluations run asynchronously via Celery to avoid blocking the web interface:

```python
from orwell_hitchens.tasks import run_full_evaluation_task

# Create evaluation record
evaluation = DraftEvaluation.objects.create(user=user, draft_text=draft)

# Trigger async task
run_full_evaluation_task.delay(evaluation.id)
```

Ensure Celery worker is running:

```bash
celery -A config worker --loglevel=info
```

## Comparison to Clinical Sovereign

| Feature | Clinical Sovereign | Orwell-Hitchens |
|---------|-------------------|-----------------|
| **Focus** | Professional LinkedIn posts | Long-form essays, articles |
| **Tone** | Detached, clinical, benevolent disinterest | Clear, argumentative, vivid |
| **Key Metrics** | Physics Engine, Zero-Kelvin Shield, Verdict Output | Clarity, Fire, Physicality, Technical |
| **Metaphors** | Systems thinking, structural villain | Concrete imagery, physical grounding |
| **Ideal Output** | Strategic frameworks, policy matrices | Persuasive essays, op-eds, analysis |

## Roadmap

- [ ] Sentence-level revision suggestions
- [ ] Specific weak verb → strong verb mappings
- [ ] Side-by-side comparison of historical vs. current performance
- [ ] Integration with popular writing tools (Google Docs, Notion)
- [ ] Export to Markdown/PDF with annotations

## Contributing

This is part of a larger Django project. To extend:

1. Add new LLM providers in `llm_evaluators.py`
2. Extend scoring logic in `analyzers.py`
3. Add new metrics to `models.py` (requires migration)
4. Customize prompts in `llm_evaluators.py`

## Credits

Inspired by:
- George Orwell's "Politics and the English Language" (1946)
- Christopher Hitchens's essays and debates
- William Zinsser's "On Writing Well"
- Strunk & White's "The Elements of Style"

## License

MIT License (see main project LICENSE)

