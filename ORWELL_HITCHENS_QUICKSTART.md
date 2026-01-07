# Orwell-Hitchens Writing Engine - Quick Start Guide

## What You Just Got

A complete Django app that evaluates your writing using principles from:
- **George Orwell**: Concrete language, active voice, clarity
- **Christopher Hitchens**: Argument structure, wit, intellectual honesty

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│  Multi-LLM Evaluation Engine                    │
│  (Claude Sonnet 4 + GPT-4o + Gemini 2.0)       │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  Scoring Framework (Weighted)                   │
│  • Orwellian Clarity (40%)                      │
│  • Hitchensian Fire (30%)                       │
│  • Vivid Physicality (20%)                      │
│  • Technical Execution (10%)                    │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  Structured Analysis                            │
│  • Abstract nouns flagged                       │
│  • Passive voice highlighted                    │
│  • Jargon detected with alternatives            │
│  • Weak verbs identified                        │
│  • Rhetorical strengths noted                   │
└─────────────────────────────────────────────────┘
```

## 5-Minute Setup

### 1. Verify Installation

The app is already installed and configured:

```bash
# Check that migrations ran successfully
python manage.py showmigrations orwell_hitchens
```

You should see:
```
orwell_hitchens
 [X] 0001_initial
```

### 2. Start the Development Server

```bash
# Terminal 1: Start Django
python manage.py runserver

# Terminal 2: Start Celery worker (for async processing)
celery -A config worker --loglevel=info
```

### 3. Create Your Writer Profile

1. Go to http://localhost:8000/admin/
2. Navigate to **Orwell Hitchens** → **Writer Profiles**
3. Click **Add Writer Profile**
4. Fill in:
   - **User**: Select your user
   - **Professional Context**: "Political Analyst" (or your actual role)
   - **Writing Domains**: "Foreign policy, international relations"
   - **Forbidden Jargon**: "synergy, leverage, robust, utilize, optimize"
   - Click **Save**

### 4. Add Sample Published Pieces (Optional)

1. Go to **Orwell Hitchens** → **Published Pieces**
2. Click **Add Published Piece**
3. Add 2-3 of your best past articles
4. Include engagement metrics if available

This helps calibrate the engine to your style.

### 5. Submit Your First Draft

1. Navigate to http://localhost:8000/orwell/
2. Paste a draft (minimum 100 characters)
3. Click **EXECUTE EVALUATION**
4. Wait 30-60 seconds for processing
5. Review your results!

## What Gets Evaluated

### The Four Dimensions

#### 1. Orwellian Clarity (40%)
**What it checks:**
- Concrete vs. abstract language
- Active vs. passive voice
- Sentence length variety
- Jargon and bureaucratic language
- Anglo-Saxon vs. Latinate words

**Example violations:**
```
❌ "The implementation of the policy was conducted by officials"
✓ "Officials implemented the policy"

❌ "There is a situation where aspects of the framework..."
✓ "The framework..."
```

#### 2. Hitchensian Fire (30%)
**What it checks:**
- Argument structure (does each paragraph advance a claim?)
- Logical scaffolding (premises → conclusions)
- Rhetorical devices (parallelism, antithesis, tricolon)
- Wit and unexpected comparisons
- Intellectual honesty (counterarguments addressed?)

**Example strength:**
```
✓ "Not only did the strategy fail in Afghanistan, it failed 
   in Iraq, and it will fail in any country where local 
   knowledge trumps aerial surveillance."
   (Tricolon + parallel structure)
```

#### 3. Vivid Physicality (20%)
**What it checks:**
- Sensory language (sight, sound, touch, smell, taste)
- Metaphor coherence (no mixed metaphors!)
- Concrete imagery vs. vague abstractions
- "Show don't tell"

**Example:**
```
❌ "The policy had negative effects"
✓ "The policy shattered communities like a hammer through glass"
```

#### 4. Technical Execution (10%)
**What it checks:**
- Grammar errors
- Redundancies ("very," "really," "actually")
- Clichés
- Flow and transitions

## Understanding Your Results

### Overall Score

- **85-100**: Publication-ready for top-tier outlets
- **70-84**: Strong, minor polishing needed
- **55-69**: Revision required
- **Below 55**: Structural rewrite needed

### Verdict

- **PUBLISH**: Meets all Orwell-Hitchens standards
- **REVISE**: Good foundation, specific issues to fix
- **REWRITE**: Structural failures, fundamental changes needed

### Flagged Issues

The interface highlights specific problems:

1. **Red boxes**: Abstract nouns to replace
2. **Yellow highlighting**: Passive voice sentences
3. **Orange table**: Jargon with suggested alternatives
4. **Purple boxes**: Weak verbs to strengthen
5. **Green boxes**: Rhetorical strengths to preserve

## Sample Test Draft

Try evaluating this intentionally flawed passage:

```
There is a situation where the implementation of strategic 
frameworks has been conducted by stakeholders. The utilization 
of robust methodologies was facilitated through the optimization 
of synergistic approaches. This impacted outcomes in a very 
significant way, which seems to suggest that future endeavors 
should leverage similar processes.
```

Expected issues:
- Abstract nouns: situation, implementation, frameworks, stakeholders, methodologies, optimization, approaches, outcomes, endeavors
- Passive voice: "has been conducted," "was facilitated"
- Jargon: stakeholders, robust, synergistic, leverage, optimize
- Weak verbs: is, has, was, seems
- Filler: very, significant

Better version (Orwell-Hitchens compliant):

```
Officials applied new strategies. These strategies combined 
intelligence-sharing with local policing—two tools that rarely 
worked alone. Crime dropped by half in six months. The lesson: 
coordination beats isolation.
```

## URLs

- **Main Evaluation Interface**: `/orwell/`
- **Evaluation History**: `/orwell/history/`
- **Detailed View**: `/orwell/evaluation/<id>/`
- **Django Admin**: `/admin/orwell_hitchens/`

## Files Created

```
orwell_hitchens/
├── __init__.py
├── admin.py                     # Django admin configuration
├── analyzers.py                 # WritingAnalyzer (consensus logic)
├── apps.py                      # App configuration
├── llm_evaluators.py            # OrwellHitchensEngine (3 LLMs)
├── models.py                    # 4 models (Profile, Piece, Evaluation, Revision)
├── tasks.py                     # Celery async task
├── urls.py                      # URL routing
├── views.py                     # 3 views (evaluate, detail, history)
├── README.md                    # Full documentation
├── migrations/
│   └── 0001_initial.py         # Database schema
└── templates/
    └── orwell_hitchens/
        ├── evaluate.html        # Main interface (brutalist design)
        ├── detail.html          # Single evaluation view
        └── history.html         # Past evaluations
```

## Integration with Clinical Sovereign

Both apps coexist:

- **Clinical Sovereign** (`/`): For LinkedIn posts, policy frameworks, detached analysis
- **Orwell-Hitchens** (`/orwell/`): For essays, op-eds, argumentative writing

They share the same architecture (multi-LLM, Celery, brutalist UI) but different evaluation criteria.

## Troubleshooting

### "No writer profile found"
Create one in Django admin: `/admin/orwell_hitchens/writerprofile/add/`

### Evaluation stuck at "PROCESSING"
Check Celery worker is running:
```bash
celery -A config worker --loglevel=info
```

### API errors in critiques
Verify API keys in `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
```

### Gemini deprecation warning
The warning about `google.generativeai` is non-critical. The package still works.
To silence it, update `orwell_hitchens/llm_evaluators.py` to use `google.genai` instead.

## Next Steps

1. **Add your published pieces** for better calibration
2. **Evaluate 3-5 drafts** to see patterns in your writing
3. **Compare scores** to your historical average
4. **Track improvement** over time in `/orwell/history/`
5. **Customize the forbidden jargon list** in your Writer Profile

## Customization

### Change Weights

Edit `analyzers.py` → `calculate_consensus()`:

```python
# Current: 40% Clarity, 30% Fire, 20% Physicality, 10% Technical
weighted = (
    float(avg_clarity) * 0.40 +
    float(avg_fire) * 0.30 +
    float(avg_physicality) * 0.20 +
    float(avg_technical) * 0.10
)
```

### Adjust Prompts

Edit `llm_evaluators.py` → `_build_evaluation_prompt()`:

```python
# Modify the framework description
# Add/remove evaluation criteria
# Change output format
```

### Add New LLMs

Add to `OrwellHitchensEngine`:

```python
def evaluate_with_new_llm(self, draft_text: str) -> str:
    # Your LLM API call
    pass

def execute_full_evaluation(self, draft_text: str) -> Dict[str, str]:
    return {
        'claude': self.evaluate_with_claude(draft_text),
        'gpt': self.evaluate_with_gpt(draft_text),
        'gemini': self.evaluate_with_gemini(draft_text),
        'new_llm': self.evaluate_with_new_llm(draft_text),  # Add here
    }
```

## Philosophy

This engine is not about writing "better" in a generic sense. It's about writing with:

1. **Orwellian clarity**: Every word must earn its place
2. **Hitchensian fire**: Every sentence must advance an argument
3. **Physical vividness**: Abstractions must become tangible
4. **Technical precision**: Grammar and flow must be invisible

The goal is not to homogenize your voice—it's to sharpen it.

---

**Ready to start?**

```bash
python manage.py runserver
# Navigate to http://localhost:8000/orwell/
# Paste your draft
# Get ruthless feedback
```

