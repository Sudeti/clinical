from django.db import models
from django.contrib.auth.models import User


class PersonaBio(models.Model):
    """
    The Clinical Sovereign Persona (Optimized Structure):
    
    I. THE ENGINE (Physics - 35%): Axiomatic Logic, Structural Ruthlessness
    II. THE ARMOR (Zero-Kelvin - 25%): Zero Ego/Anger, Benevolent Disinterest
    III. THE WEAPON (The Verdict - 20%): High-Density Output, Slightly Venomous
    IV. THE KINETIC (Action - Critical): Artifacts, Velocity
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    professional_title = models.CharField(
        max_length=200,
        help_text="e.g., 'Diplomatic Desk Officer, European Security'"
    )
    
    core_expertise = models.TextField(
        help_text="THE ENGINE: Areas of domain expertise (First Principles, Structural Physics)"
    )
    
    writing_axioms = models.TextField(
        help_text="THE WEAPON: Non-negotiable writing principles (High-Density Verdicts, Slightly Venomous)",
        default="1. Zero emotional language (Zero-Kelvin)\n2. Structural analysis only (Physics Engine)\n3. Verdicts, not opinions (The Weapon)\n4. Slightly venomous to mediocrity (Scalpel Edge)"
    )
    
    target_audience = models.CharField(
        max_length=300,
        default="GS-level analysts, ambassadors, policy professionals",
        help_text="THE KINETIC: Target audience (Strategic Centrality - Thin Tail nodes)"
    )
    
    forbidden_terms = models.TextField(
        help_text="THE ARMOR: Comma-separated banned words (Zero-Kelvin Shield)",
        default="excited, happy, honored, thrilled, blessed, passionate, amazing, incredible"
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Persona: {self.user.username}"


class ArchivedPost(models.Model):
    """
    Historical record of published content.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=300)
    content = models.TextField()
    published_date = models.DateField()
    
    linkedin_saves = models.IntegerField(default=0)
    linkedin_comments = models.IntegerField(default=0)
    linkedin_shares = models.IntegerField(default=0)
    high_value_engagement = models.IntegerField(
        default=0,
        help_text="Comments from GS/Ambassador-level"
    )
    
    clarity_rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 11)],
        null=True,
        blank=True,
        help_text="Your retrospective clarity score (1-10)"
    )
    
    notes = models.TextField(blank=True, help_text="What worked, what failed")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-published_date']
    
    def __str__(self):
        return f"{self.published_date} - {self.title}"


class DraftCritique(models.Model):
    """
    LLM evaluation records.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    draft_text = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    claude_critique = models.TextField(blank=True)
    gpt_critique = models.TextField(blank=True)
    gemini_critique = models.TextField(blank=True)
    
    avg_clinical_score = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True
    )
    
    consensus_verdict = models.CharField(
        max_length=20,
        choices=[
            ('CLEAR', 'Clear for Publication'),
            ('REVISE', 'Requires Revision'),
            ('REJECT', 'Structural Failure')
        ],
        blank=True
    )
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Critique {self.id} - {self.submitted_at.strftime('%Y-%m-%d %H:%M')}"

class CommentGeneration(models.Model):
    """
    Generated comment options for LinkedIn posts/comments.
    Part of the "Arbitrage Comment Engine" - high-frequency engagement tool.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Source content
    source_url = models.URLField(
        blank=True,
        help_text="LinkedIn post/comment URL (optional)"
    )
    source_text = models.TextField(
        help_text="The original post or comment text to respond to"
    )
    
    # Three generated comment options
    comment_option_1 = models.TextField(
        help_text="First comment option (analytical angle)"
    )
    comment_option_2 = models.TextField(
        help_text="Second comment option (framework angle)"
    )
    comment_option_3 = models.TextField(
        help_text="Third comment option (counterpoint angle)"
    )
    
    # Metadata
    selected_option = models.IntegerField(
        null=True,
        blank=True,
        choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3')],
        help_text="Which option the user selected"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment Generation {self.id} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"