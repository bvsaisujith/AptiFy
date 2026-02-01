from ninja import Router, Schema
from django.shortcuts import get_object_or_404
from typing import List
from analysis.services.inference_engine import InferenceEngine
from analysis.models import GapAnalysisReport, SkillAnalysis
from assignments.models import AssignmentAttempt
from aptify.auth import django_auth

router = Router()

class ReportSchema(Schema):
    student_name: str
    primary_gap: str
    secondary_gap: str
    confidence_level: float
    recommendation: str
    skill_traversal_path: List[str]
    generated_at: str

class ReportListItemSchema(Schema):
    attempt_id: int
    primary_gap: str
    secondary_gap: str
    confidence_level: float
    recommendation: str
    generated_at: str

@router.get("/reports", auth=django_auth, response=List[ReportListItemSchema])
def list_reports(request):
    """List current user's gap analysis reports (latest first)."""
    reports = GapAnalysisReport.objects.filter(student=request.user).select_related("attempt").order_by("-generated_at")
    return [
        {
            "attempt_id": r.attempt_id,
            "primary_gap": r.primary_gap,
            "secondary_gap": r.secondary_gap,
            "confidence_level": r.confidence_level,
            "recommendation": r.recommendation,
            "generated_at": r.generated_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for r in reports
    ]

@router.post("/generate/{attempt_id}", auth=django_auth, response=ReportSchema)
def generate_analysis(request, attempt_id: int):
    """
    Triggers the AI Inference Engine for a specific attempt.
    Returns the generated learning gap report.
    """
    attempt = get_object_or_404(AssignmentAttempt, id=attempt_id, user=request.user)
    report = InferenceEngine.analyze_attempt(attempt.id)
    
    return {
        "student_name": report.student.username,
        "primary_gap": report.primary_gap,
        "secondary_gap": report.secondary_gap,
        "confidence_level": report.confidence_level,
        "recommendation": report.recommendation,
        "skill_traversal_path": report.skill_traversal_path,
        "generated_at": report.generated_at.strftime("%Y-%m-%d %H:%M:%S")
    }

@router.get("/report/{attempt_id}", auth=django_auth, response=ReportSchema)
def get_report(request, attempt_id: int):
    report = get_object_or_404(GapAnalysisReport, attempt_id=attempt_id, student=request.user)
    return {
        "student_name": report.student.username,
        "primary_gap": report.primary_gap,
        "secondary_gap": report.secondary_gap,
        "confidence_level": report.confidence_level,
        "recommendation": report.recommendation,
        "skill_traversal_path": report.skill_traversal_path,
        "generated_at": report.generated_at.strftime("%Y-%m-%d %H:%M:%S")
    }
