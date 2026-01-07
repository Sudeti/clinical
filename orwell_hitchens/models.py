from django.db import models
from django.contrib.auth.models import User


class WriterProfile(models.Model):
    """
    The Orwell-Hitchens Writing Profile:
    
    I. ORWELLIAN CLARITY (40%): Concrete over abstract, active voice, short punches
    II. HITCHENSIAN FIRE (30%): Argument structure, wit, intellectual honesty
    III. VIVID PHYSICALITY (20%): Sensory language, coherent metaphors
    IV. TECHNICAL EXECUTION (10%): Grammar, redundancies, flow
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    professional_context = models.CharField(
        max_length=200,
        help_text="e.g., 'Foreign Policy Analyst', 'Political Commentator'"
    )
    
    writing_domains = models.TextField(
        help_text="Your areas of expertise (for calibration and context)"
    )
    
    style_preferences = models.TextField(
        help_text="Your non-negotiable writing principles",
        default="1. Concrete over abstract (Orwell)\n2. Every sentence advances an argument (Hitchens)\n3. Anglo-Saxon words over Latinate\n4. Active voice carries conviction"
    )
    
    target_publications = models.CharField(
        max_length=300,
        default="The Atlantic, Foreign Affairs, The New Yorker",
        help_text="Target publications/platforms for calibration"
    )
    
    forbidden_jargon = models.TextField(
        help_text="Comma-separated bureaucratic euphemisms to avoid",
        default="synergy, leverage, robust, stakeholder, impact (as verb), utilize, facilitate, optimize"
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Writer Profile: {self.user.username}"


class PublishedPiece(models.Model):
    """
    Historical record of published writing for calibration.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=300)
    content = models.TextField()
    published_date = models.DateField()
    publication = models.CharField(max_length=200, blank=True)
    
    # Engagement metrics
    social_shares = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    citation_count = models.IntegerField(
        default=0,
        help_text="Times cited or referenced by others"
    )
    
    # Self-assessment
    clarity_rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 11)],
        null=True,
        blank=True,
        help_text="Your retrospective Orwellian clarity score (1-10)"
    )
    impact_rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 11)],
        null=True,
        blank=True,
        help_text="Your retrospective impact/persuasiveness score (1-10)"
    )
    
    notes = models.TextField(blank=True, help_text="What worked, what failed")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-published_date']
    
    def __str__(self):
        return f"{self.published_date} - {self.title}"


class DraftEvaluation(models.Model):
    """
    Multi-LLM evaluation of writing drafts using Orwell-Hitchens framework.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    draft_text = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    # Raw LLM critiques
    claude_critique = models.TextField(blank=True)
    gpt_critique = models.TextField(blank=True)
    gemini_critique = models.TextField(blank=True)
    
    # Consensus scores (averaged across LLMs)
    orwellian_clarity_score = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Concrete language, active voice, sentence variety (0-100)"
    )
    hitchensian_fire_score = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Argument structure, wit, intellectual honesty (0-100)"
    )
    vivid_physicality_score = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Sensory language, metaphor coherence (0-100)"
    )
    technical_execution_score = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Grammar, redundancies, flow (0-100)"
    )
    
    # Overall weighted score
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Weighted average: Clarity 40%, Fire 30%, Physicality 20%, Technical 10%"
    )
    
    # Historical comparison
    historical_avg_score = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Average score computed from top published pieces"
    )
    
    # Structured analysis
    from django.db.models import JSONField
    
    abstract_nouns = JSONField(
        null=True,
        blank=True,
        default=list,
        help_text="Flagged abstract words: situation, aspect, factor, etc."
    )
    passive_voice_sentences = JSONField(
        null=True,
        blank=True,
        default=list,
        help_text="Sentence indices with passive voice"
    )
    jargon_violations = JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text="Detected jargon/euphemisms with suggested replacements"
    )
    weak_verbs = JSONField(
        null=True,
        blank=True,
        default=list,
        help_text="Weak verb instances flagged for replacement"
    )
    rhetorical_highlights = JSONField(
        null=True,
        blank=True,
        default=list,
        help_text="Strong rhetorical devices detected"
    )
    
    # Coaching fields (help writer improve over time)
    diagnostic_summary = models.TextField(
        blank=True,
        help_text="Core weaknesses identified with examples"
    )
    before_after_examples = JSONField(
        null=True,
        blank=True,
        default=list,
        help_text="Before/after rewrites showing improvements"
    )
    strengths_to_amplify = JSONField(
        null=True,
        blank=True,
        default=list,
        help_text="Things the writer is doing RIGHT to double down on"
    )
    recurring_patterns = JSONField(
        null=True,
        blank=True,
        default=list,
        help_text="Habits and tendencies detected across the draft"
    )
    concrete_next_steps = JSONField(
        null=True,
        blank=True,
        default=list,
        help_text="Specific actionable improvements for next draft"
    )
    one_sentence_verdict = models.TextField(
        blank=True,
        help_text="Concise summary of overall assessment"
    )
    
    # Verdict
    consensus_verdict = models.CharField(
        max_length=20,
        choices=[
            ('PROCESSING', 'Processing'),
            ('PUBLISH', 'Ready to Publish'),
            ('REVISE', 'Requires Revision'),
            ('REWRITE', 'Structural Rewrite Needed')
        ],
        blank=True
    )
    
    class Meta:
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['user', 'submitted_at']),
            models.Index(fields=['submitted_at']),
        ]
    
    def __str__(self):
        return f"Evaluation {self.id} - {self.submitted_at.strftime('%Y-%m-%d %H:%M')}"


class SuggestedRevision(models.Model):
    """
    LLM-generated revision suggestions for flagged issues.
    """
    evaluation = models.ForeignKey(DraftEvaluation, on_delete=models.CASCADE, related_name='revisions')
    llm_source = models.CharField(
        max_length=20,
        choices=[('claude', 'Claude'), ('gpt', 'GPT'), ('gemini', 'Gemini')]
    )
    
    original_text = models.TextField(help_text="The problematic passage")
    suggested_text = models.TextField(help_text="The improved version")
    issue_type = models.CharField(
        max_length=50,
        help_text="e.g., 'passive_voice', 'abstract_noun', 'weak_verb', 'jargon'"
    )
    explanation = models.TextField(help_text="Why this change improves the writing")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Revision ({self.issue_type}) - {self.evaluation.id}"
