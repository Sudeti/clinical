from celery import shared_task
from decimal import Decimal
from .models import DraftEvaluation, WriterProfile, PublishedPiece
from .llm_evaluators import OrwellHitchensEngine
from .analyzers import WritingAnalyzer


@shared_task(bind=True, max_retries=2)
def run_full_evaluation_task(self, record_id):
    """
    Execute full Orwell-Hitchens evaluation for a draft.
    """
    try:
        record = DraftEvaluation.objects.get(id=record_id)
        
        # Get or create a default WriterProfile
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
        
        published_pieces = PublishedPiece.objects.filter(user=record.user).order_by('-published_date')[:5]
        
        # Execute the heavy LLM calls
        engine = OrwellHitchensEngine(profile, published_pieces)
        critiques = engine.execute_full_evaluation(record.draft_text)

        # Calculate consensus
        consensus = WritingAnalyzer.calculate_consensus(critiques)

        # Persist raw LLM outputs
        record.claude_critique = critiques.get('claude', '')
        record.gpt_critique = critiques.get('gpt', '')
        record.gemini_critique = critiques.get('gemini', '')

        # Populate structured fields
        record.orwellian_clarity_score = consensus.get('orwellian_clarity_score')
        record.hitchensian_fire_score = consensus.get('hitchensian_fire_score')
        record.vivid_physicality_score = consensus.get('vivid_physicality_score')
        record.technical_execution_score = consensus.get('technical_execution_score')
        record.overall_score = consensus.get('overall_score')
        record.consensus_verdict = consensus.get('consensus_verdict')
        
        record.abstract_nouns = consensus.get('abstract_nouns', [])
        record.passive_voice_sentences = consensus.get('passive_voice_sentences', [])
        record.jargon_violations = consensus.get('jargon_violations', {})
        record.weak_verbs = consensus.get('weak_verbs', [])
        record.rhetorical_highlights = consensus.get('rhetorical_highlights', [])
        
        # Coaching fields
        record.diagnostic_summary = consensus.get('diagnostic_summary', '')
        record.before_after_examples = consensus.get('before_after_examples', [])
        record.strengths_to_amplify = consensus.get('strengths_to_amplify', [])
        record.recurring_patterns = consensus.get('recurring_patterns', [])
        record.concrete_next_steps = consensus.get('concrete_next_steps', [])
        record.one_sentence_verdict = consensus.get('one_sentence_verdict', '')

        # Compute historical average from top published pieces
        try:
            top_pieces = sorted(
                list(published_pieces),
                key=lambda p: (p.citation_count or 0) + (p.social_shares or 0) + (p.comments_count or 0),
                reverse=True
            )[:3]

            hist_scores = []
            for piece in top_pieces:
                # Use the same engine to score historical pieces (lightweight)
                piece_critiques = engine.execute_full_evaluation(piece.content[:2000])
                piece_consensus = WritingAnalyzer.calculate_consensus(piece_critiques)
                if piece_consensus.get('overall_score') is not None:
                    hist_scores.append(piece_consensus.get('overall_score'))

            if hist_scores:
                # compute numeric average
                avg_hist = sum([float(s) for s in hist_scores]) / len(hist_scores)
                record.historical_avg_score = Decimal(str(avg_hist)).quantize(Decimal('0.1'))
        except Exception:
            # Don't block on historical scoring failures
            pass

        record.save()
        
    except DraftEvaluation.DoesNotExist:
        # Record was deleted before task could process, don't retry
        return
    except Exception as exc:
        # If an API fails, wait 30 seconds and try again (up to max_retries)
        self.retry(exc=exc, countdown=30)

