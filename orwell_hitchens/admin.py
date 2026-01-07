from django.contrib import admin
from .models import WriterProfile, PublishedPiece, DraftEvaluation, SuggestedRevision


@admin.register(WriterProfile)
class WriterProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'professional_context', 'updated_at']
    search_fields = ['user__username', 'professional_context']
    readonly_fields = ['updated_at']


@admin.register(PublishedPiece)
class PublishedPieceAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'published_date', 'publication', 'citation_count', 'social_shares']
    list_filter = ['published_date', 'publication']
    search_fields = ['title', 'user__username', 'publication']
    date_hierarchy = 'published_date'
    readonly_fields = ['created_at']


@admin.register(DraftEvaluation)
class DraftEvaluationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'submitted_at', 'overall_score', 'consensus_verdict'
    ]
    list_filter = ['consensus_verdict', 'submitted_at']
    search_fields = ['user__username', 'draft_text']
    date_hierarchy = 'submitted_at'
    readonly_fields = ['submitted_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'draft_text', 'submitted_at', 'consensus_verdict')
        }),
        ('Consensus Scores', {
            'fields': (
                'overall_score',
                'orwellian_clarity_score',
                'hitchensian_fire_score',
                'vivid_physicality_score',
                'technical_execution_score',
                'historical_avg_score'
            )
        }),
        ('Structured Analysis', {
            'fields': (
                'abstract_nouns',
                'passive_voice_sentences',
                'jargon_violations',
                'weak_verbs',
                'rhetorical_highlights'
            ),
            'classes': ('collapse',)
        }),
        ('Raw LLM Critiques', {
            'fields': ('claude_critique', 'gpt_critique', 'gemini_critique'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SuggestedRevision)
class SuggestedRevisionAdmin(admin.ModelAdmin):
    list_display = ['evaluation', 'llm_source', 'issue_type', 'created_at']
    list_filter = ['llm_source', 'issue_type', 'created_at']
    search_fields = ['evaluation__id', 'original_text', 'suggested_text']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
