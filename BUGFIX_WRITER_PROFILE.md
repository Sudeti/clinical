# Bug Fix: WriterProfile Auto-Creation

## Problem

The Celery task was failing with this error:

```
orwell_hitchens.models.WriterProfile.DoesNotExist: WriterProfile matching query does not exist.
```

This happened when users submitted drafts for evaluation without first creating a `WriterProfile` in Django admin.

## Root Cause

In `orwell_hitchens/tasks.py`, the task was using:

```python
profile = WriterProfile.objects.get(user=record.user)
```

This would raise `DoesNotExist` if the user hadn't created a profile yet, causing the task to retry indefinitely and eventually fail.

## Solution

Changed to auto-create a default `WriterProfile` with sensible defaults:

```python
profile, created = WriterProfile.objects.get_or_create(
    user=record.user,
    defaults={
        'professional_context': 'Writer',
        'writing_domains': 'General writing',
        'style_preferences': '1. Concrete over abstract (Orwell)\n2. Every sentence advances an argument (Hitchens)\n3. Anglo-Saxon words over Latinate\n4. Active voice carries conviction',
        'target_publications': 'General publications',
        'forbidden_jargon': 'synergy, leverage, robust, stakeholder, impact (as verb), utilize, facilitate, optimize'
    }
)
```

## Additional Improvements

1. **Better error handling for deleted records**: If a `DraftEvaluation` is deleted between submission and processing, the task now exits gracefully instead of retrying:

```python
except DraftEvaluation.DoesNotExist:
    # Record was deleted before task could process, don't retry
    return
```

2. **Removed unnecessary warning**: Removed the warning message in the view that told users they needed to create a profile, since it's now auto-created.

## Impact

### Before
- ❌ Users had to create a `WriterProfile` in Django admin before using the system
- ❌ Task would fail and retry if profile didn't exist
- ❌ Confusing error messages in Celery logs

### After
- ✅ Users can submit drafts immediately without setup
- ✅ Default profile auto-created on first use
- ✅ Users can customize their profile later in Django admin for better calibration
- ✅ Graceful handling of edge cases (deleted records)

## User Experience

### New User Flow

1. **First time**: User navigates to `/orwell/`, pastes draft, clicks submit
2. **System**: Auto-creates default `WriterProfile`, evaluates draft
3. **User**: Sees results in ~60 seconds
4. **Later (optional)**: User customizes profile in Django admin for better calibration

### Existing User Flow

No changes - if a `WriterProfile` already exists, it continues to use it.

## Testing

All tests pass:

```bash
python manage.py test orwell_hitchens
# Ran 8 tests in 0.939s
# OK
```

## Files Modified

1. `orwell_hitchens/tasks.py` - Auto-create profile, better error handling
2. `orwell_hitchens/views.py` - Removed unnecessary warning

## Recommendation

Users should still create/customize their `WriterProfile` in Django admin for best results:

- Add their professional context
- List their writing domains
- Specify target publications
- Add personal forbidden jargon
- Upload past published pieces for calibration

But the system now works out-of-the-box without requiring this setup.

