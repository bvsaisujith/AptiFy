from django.contrib import admin
from .models import GapAnalysisReport, SkillAnalysis

class SkillAnalysisInline(admin.TabularInline):
    model = SkillAnalysis
    extra = 0

@admin.register(GapAnalysisReport)
class GapAnalysisReportAdmin(admin.ModelAdmin):
    list_display = ('student', 'primary_gap', 'confidence_level', 'generated_at')
    inlines = [SkillAnalysisInline]
    list_filter = ('generated_at',)
    search_fields = ('student__username', 'primary_gap')

@admin.register(SkillAnalysis)
class SkillAnalysisAdmin(admin.ModelAdmin):
    list_display = ('report', 'skill_name', 'status', 'score_impact')
    list_filter = ('status',)
