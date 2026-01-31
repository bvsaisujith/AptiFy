from django.db import models
from django.conf import settings
from assignments.models import AssignmentAttempt

class GapAnalysisReport(models.Model):
    """
    Stores the AI-generated intelligence report for a student's attempt.
    """
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    attempt = models.OneToOneField(AssignmentAttempt, related_name='analysis_report', on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    # Core Findings
    primary_gap = models.CharField(max_length=255, help_text="The root cause learning gap identified.")
    secondary_gap = models.CharField(max_length=255, blank=True, help_text="Secondary areas of improvement.")
    
    # Analysis Details
    confidence_level = models.FloatField(help_text="Confidence in the analysis (0-100%).")
    recommendation = models.TextField(help_text="Personalized recommendation for the student.")
    
    # Visual/Graph Data (Stored as JSON for flexibility in frontend rendering)
    skill_traversal_path = models.JSONField(default=list, help_text="Path traversed in dependency graph.")
    
    def __str__(self):
        return f"Report for {self.student} - {self.primary_gap}"

class SkillAnalysis(models.Model):
    """
    Detailed status of individual skills for a report.
    """
    class Status(models.TextChoices):
        STRONG = 'STRONG', 'Strong'
        WEAK = 'WEAK', 'Weak'
        GAP = 'GAP', 'Gap Detected'

    report = models.ForeignKey(GapAnalysisReport, related_name='skill_analyses', on_delete=models.CASCADE)
    skill_name = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=Status.choices)
    score_impact = models.FloatField(default=0.0, help_text="How much this skill impacted the score.")

    def __str__(self):
        return f"{self.skill_name}: {self.status}"
