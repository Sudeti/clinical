from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PersonaBio, ArchivedPost, DraftCritique, CommentGeneration
from .llm_evaluators import SovereignCriticEngine
from .analyzers import CritiqueAnalyzer  # NEW IMPORT
from .comment_generator import CommentGenerator


@login_required
def evaluate_draft(request):
    """Main evaluation interface - Async Version."""
    persona, _ = PersonaBio.objects.get_or_create(user=request.user)
    archived_posts = ArchivedPost.objects.filter(user=request.user)[:5]
    recent_critiques = DraftCritique.objects.filter(user=request.user)[:5]
    
    context = {
        'persona': persona,
        'archived_posts': archived_posts,
        'recent_critiques': recent_critiques
    }
    
    if request.method == 'POST':
        draft_text = request.POST.get('draft_text', '').strip()
        
        if not draft_text or len(draft_text) < 100:
            messages.error(request, "Draft invalid or too short.")
            return render(request, 'evaluate.html', context)
        
        # 1. Create the record immediately in a 'PENDING' state
        critique_record = DraftCritique.objects.create(
            user=request.user,
            draft_text=draft_text,
            consensus_verdict='PROCESSING' # Ensure your model choice allows this
        )

        # 2. TRIGGER THE TASK (This is the magic part)
        from .tasks import run_full_critique_task
        run_full_critique_task.delay(critique_record.id)

        messages.success(request, "Sovereign analysis started. Refresh this page in ~30 seconds.")
        return redirect('evaluate_draft')
    
    return render(request, 'evaluate.html', context)


@login_required
def generate_comment(request):
    """
    Arbitrage Comment Engine - Generate 3 clinical comment options
    for LinkedIn posts/comments.
    """
    persona, created = PersonaBio.objects.get_or_create(
        user=request.user,
        defaults={
            'professional_title': 'Policy Analyst',
            'core_expertise': 'To be configured',
        }
    )
    
    # Check if persona needs configuration
    if persona.core_expertise == 'To be configured':
        messages.warning(
            request, 
            "⚠ Configure your Persona in Django Admin for better comment generation."
        )
    
    # Get archived posts for tone calibration
    archived_posts = ArchivedPost.objects.filter(user=request.user)
    recent_generations = CommentGeneration.objects.filter(user=request.user)[:5]
    
    context = {
        'persona': persona,
        'archived_posts': archived_posts,
        'recent_generations': recent_generations
    }
    
    if request.method == 'POST':
        source_url = request.POST.get('source_url', '').strip()
        source_text = request.POST.get('source_text', '').strip()
        
        if not source_text:
            messages.error(request, "Source text or URL required.")
            return render(request, 'generate_comment.html', context)
        
        if len(source_text) < 20:
            messages.error(request, "Source text too short (minimum 20 characters).")
            return render(request, 'generate_comment.html', context)
        
        # Generate comment options
        generator = CommentGenerator(persona, archived_posts)
        options = generator.generate_three_options(source_text)
        
        # Save to database
        comment_gen = CommentGeneration.objects.create(
            user=request.user,
            source_url=source_url if source_url else '',
            source_text=source_text,
            comment_option_1=options['option_1'],
            comment_option_2=options['option_2'],
            comment_option_3=options['option_3']
        )
        
        messages.success(
            request,
            f"Generated 3 comment options (Generation #{comment_gen.id}). "
            "Select the best one to copy."
        )
        
        context['current_generation'] = comment_gen
    
    return render(request, 'generate_comment.html', context)


@login_required
def select_comment_option(request, generation_id, option_number):
    """
    Mark which comment option was selected.
    """
    try:
        comment_gen = CommentGeneration.objects.get(
            id=generation_id,
            user=request.user
        )
        comment_gen.selected_option = option_number
        comment_gen.save()
        messages.success(request, f"Option {option_number} marked as selected.")
        
        # Get persona and context for rendering
        persona, _ = PersonaBio.objects.get_or_create(user=request.user)
        archived_posts = ArchivedPost.objects.filter(user=request.user)
        recent_generations = CommentGeneration.objects.filter(user=request.user)[:5]
        
        return render(request, 'generate_comment.html', {
            'persona': persona,
            'archived_posts': archived_posts,
            'recent_generations': recent_generations,
            'current_generation': comment_gen
        })
    except CommentGeneration.DoesNotExist:
        messages.error(request, "Comment generation not found.")
        return redirect('generate_comment')