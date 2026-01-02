from django.contrib import admin
from django.utils.html import format_html
from .models import PersonaBio, ArchivedPost, DraftCritique, CommentGeneration


@admin.register(PersonaBio)
class PersonaBioAdmin(admin.ModelAdmin):
    list_display = ['user', 'professional_title', 'updated_at']


@admin.register(ArchivedPost)
class ArchivedPostAdmin(admin.ModelAdmin):
    list_display = ['published_date', 'title', 'linkedin_saves', 'high_value_engagement']
    list_filter = ['published_date']


@admin.register(DraftCritique)
class DraftCritiqueAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'submitted_at', 
        'avg_clinical_score', 'verdict_display'  # UPDATED
    ]
    list_filter = ['submitted_at', 'consensus_verdict']  # UPDATED
    readonly_fields = ['submitted_at', 'avg_clinical_score', 'consensus_verdict']
    
    def verdict_display(self, obj):
        """Color-coded verdict display."""
        colors = {
            'CLEAR': '#00ff00',
            'REVISE': '#ffff00',
            'REJECT': '#ff0000'
        }
        color = colors.get(obj.consensus_verdict, '#ffffff')
        return format_html(
            '<strong style="color: {};">{}</strong>',
            color,
            obj.consensus_verdict or 'PENDING'
        )
    verdict_display.short_description = 'Verdict'


@admin.register(CommentGeneration)
class CommentGenerationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'selected_option', 'source_preview']
    list_filter = ['created_at', 'selected_option']
    readonly_fields = ['created_at']
    search_fields = ['source_text', 'source_url']
    
    def source_preview(self, obj):
        """Preview of source text."""
        return obj.source_text[:100] + "..." if len(obj.source_text) > 100 else obj.source_text
    source_preview.short_description = 'Source Preview'
