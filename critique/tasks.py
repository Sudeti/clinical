from celery import shared_task
from .models import DraftCritique, PersonaBio, ArchivedPost
from .llm_evaluators import SovereignCriticEngine
from .analyzers import CritiqueAnalyzer

@shared_task(bind=True, max_retries=2)
def run_full_critique_task(self, record_id):
    try:
        record = DraftCritique.objects.get(id=record_id)
        persona = PersonaBio.objects.get(user=record.user)
        archived_posts = ArchivedPost.objects.filter(user=record.user)[:5]
        
        # Execute the heavy LLM calls
        critic_engine = SovereignCriticEngine(persona, archived_posts)
        critiques = critic_engine.execute_full_critique(record.draft_text)
        
        # Calculate consensus
        consensus = CritiqueAnalyzer.calculate_consensus(critiques)
        
        # Update the record
        record.claude_critique = critiques['claude']
        record.gpt_critique = critiques['gpt']
        record.gemini_critique = critiques['gemini']
        record.avg_clinical_score = consensus['avg_clinical_score']
        record.consensus_verdict = consensus['consensus_verdict']
        record.save()
        
    except Exception as exc:
        # If an API fails, wait 30 seconds and try again
        self.retry(exc=exc, countdown=30)