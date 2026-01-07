# Gemini API Migration Guide

## Current Warning

You're seeing this warning when running the app:

```
FutureWarning: All support for the `google.generativeai` package has ended. 
Please switch to the `google.genai` package as soon as possible.
```

This warning appears in both:
- `critique/llm_evaluators.py` (Clinical Sovereign)
- `orwell_hitchens/llm_evaluators.py` (Orwell-Hitchens)

## Why It's Not Critical

The old `google.generativeai` package **still works** and will continue to work for the foreseeable future. The warning is just a heads-up that Google wants you to migrate to the newer `google.genai` package.

## How to Migrate (Optional)

### Step 1: Install New Package

```bash
source venv/bin/activate
pip install google-genai
pip uninstall google-generativeai
```

### Step 2: Update `critique/llm_evaluators.py`

Replace:

```python
import google.generativeai as genai

# In __init__:
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# In evaluate_with_gemini:
model = genai.GenerativeModel("gemini-3-pro-preview")
response = model.generate_content(
    full_prompt,
    generation_config=genai.types.GenerationConfig(
        temperature=0.3,
        max_output_tokens=2000
    )
)
return response.text
```

With:

```python
from google import genai
from google.genai import types

# In __init__:
self.gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# In evaluate_with_gemini:
response = self.gemini_client.models.generate_content(
    model="gemini-3-pro-preview",
    contents=full_prompt,
    config=types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=2000
    )
)
return response.text
```

### Step 3: Update `orwell_hitchens/llm_evaluators.py`

Replace:

```python
import google.generativeai as genai

# In __init__:
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# In evaluate_with_gemini:
model = genai.GenerativeModel("gemini-2.0-flash-exp")
response = model.generate_content(
    full_prompt,
    generation_config=genai.types.GenerationConfig(
        temperature=0.2,
        max_output_tokens=3000,
        response_mime_type="application/json"
    )
)
return response.text
```

With:

```python
from google import genai
from google.genai import types

# In __init__:
self.gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# In evaluate_with_gemini:
response = self.gemini_client.models.generate_content(
    model="gemini-2.0-flash-exp",
    contents=full_prompt,
    config=types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=3000,
        response_mime_type="application/json"
    )
)
return response.text
```

### Step 4: Update `requirements.txt`

Remove:
```
google-generativeai==0.x.x
```

Add:
```
google-genai
```

### Step 5: Test

```bash
python manage.py test critique
python manage.py test orwell_hitchens
```

Both test suites should still pass.

## If You Choose Not to Migrate

**That's totally fine!** The old package works perfectly. You can safely ignore the warning. The functionality is identical.

To suppress the warning (without migrating), add this to the top of both `llm_evaluators.py` files:

```python
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
```

## Model Name Changes

When you do migrate, check if model names have changed:

| Old Name (deprecated) | New Name (check docs) |
|-----------------------|-----------------------|
| `gemini-3-pro-preview` | May have changed to `gemini-2.0-flash` or similar |
| `gemini-2.0-flash-exp` | May be stable now as `gemini-2.0-flash` |

Check the latest docs: https://ai.google.dev/gemini-api/docs

## Estimated Time

- **If you migrate**: 15-20 minutes (install, update, test)
- **If you don't**: 0 minutes (just ignore the warning)

## Recommendation

**For now**: Ignore the warning. The old API works fine.

**Later (when you have time)**: Migrate to the new package during a maintenance window. Test thoroughly to ensure model names and API responses are still compatible with your parsing logic in `analyzers.py`.

