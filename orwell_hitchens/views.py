from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DraftEvaluation, WriterProfile, PublishedPiece
from .tasks import run_full_evaluation_task
from .analyzers import WritingAnalyzer


@login_required
def evaluate_draft(request):
    """
    Main view for submitting drafts and viewing evaluations.
    """
    if request.method == 'POST':
        draft_text = request.POST.get('draft_text', '').strip()
        
        if len(draft_text) < 100:
            messages.error(request, "Draft must be at least 100 characters.")
            return redirect('orwell_evaluate')
        
        # Create the evaluation record
        evaluation = DraftEvaluation.objects.create(
            user=request.user,
            draft_text=draft_text,
            consensus_verdict='PROCESSING'
        )
        
        # Trigger async evaluation
        run_full_evaluation_task.delay(evaluation.id)
        
        messages.success(
            request,
            f"Draft submitted for Orwell-Hitchens evaluation. Evaluation ID: {evaluation.id}"
        )
        return redirect('orwell_evaluate')
    
    # GET request: show form and latest evaluation
    # Profile will be auto-created on first evaluation if it doesn't exist
    profile = WriterProfile.objects.filter(user=request.user).first()
    
    current_evaluation = DraftEvaluation.objects.filter(user=request.user).first()
    published_pieces = PublishedPiece.objects.filter(user=request.user)[:5]
    
    # Highlight passive voice sentences in draft
    highlighted_draft = None
    if current_evaluation and current_evaluation.passive_voice_sentences:
        highlighted_draft = WritingAnalyzer.highlight_sentences(
            current_evaluation.draft_text,
            current_evaluation.passive_voice_sentences
        )
    
    context = {
        'profile': profile,
        'current_evaluation': current_evaluation,
        'published_pieces': published_pieces,
        'highlighted_draft': highlighted_draft,
    }
    
    return render(request, 'orwell_hitchens/evaluate.html', context)


@login_required
def evaluation_detail(request, evaluation_id):
    """
    View detailed evaluation results.
    """
    evaluation = get_object_or_404(DraftEvaluation, id=evaluation_id, user=request.user)
    
    # Highlight passive voice sentences
    highlighted_draft = None
    if evaluation.passive_voice_sentences:
        highlighted_draft = WritingAnalyzer.highlight_sentences(
            evaluation.draft_text,
            evaluation.passive_voice_sentences
        )
    
    context = {
        'evaluation': evaluation,
        'highlighted_draft': highlighted_draft,
    }
    
    return render(request, 'orwell_hitchens/detail.html', context)


@login_required
def evaluation_history(request):
    """
    View all past evaluations.
    """
    evaluations = DraftEvaluation.objects.filter(user=request.user)[:20]
    
    context = {
        'evaluations': evaluations,
    }
    
    return render(request, 'orwell_hitchens/history.html', context)
