from celery import shared_task
from decimal import Decimal
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

        # Calculate consensus (now returns artifact, forbidden_alternatives, sentence_triggers)
        consensus = CritiqueAnalyzer.calculate_consensus(critiques)

        # Persist raw LLM outputs
        record.claude_critique = critiques.get('claude', '')
        record.gpt_critique = critiques.get('gpt', '')
        record.gemini_critique = critiques.get('gemini', '')

        # Populate structured fields
        record.avg_clinical_score = consensus.get('avg_clinical_score')
        record.consensus_verdict = consensus.get('consensus_verdict')
        record.artifact = consensus.get('artifact', '')
        record.forbidden_alternatives = consensus.get('forbidden_alternatives', {})
        record.sentence_triggers = consensus.get('sentence_triggers', [])

        # Compute historical average clinical score from top archived posts
        try:
            top_posts = sorted(
                list(archived_posts),
                key=lambda p: (p.high_value_engagement or 0) + (p.linkedin_comments or 0) + (p.linkedin_saves or 0) + (p.linkedin_shares or 0),
                reverse=True
            )[:3]

            hist_scores = []
            for post in top_posts:
                # Use the same critic engine to score historical posts (lightweight)
                post_critiques = critic_engine.execute_full_critique(post.content[:1500])
                post_consensus = CritiqueAnalyzer.calculate_consensus(post_critiques)
                if post_consensus.get('avg_clinical_score') is not None:
                    hist_scores.append(post_consensus.get('avg_clinical_score'))

            if hist_scores:
                # compute numeric average
                avg_hist = sum([float(s) for s in hist_scores]) / len(hist_scores)
                record.historical_avg_clinical_score = Decimal(str(avg_hist)).quantize(Decimal('0.1'))
        except Exception:
            # Don't block on historical scoring failures
            pass

        record.save()
        
    except Exception as exc:
        # If an API fails, wait 30 seconds and try again
        self.retry(exc=exc, countdown=30)