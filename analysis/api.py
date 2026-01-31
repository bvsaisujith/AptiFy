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

@router.post("/generate/{attempt_id}", auth=django_auth, response=ReportSchema)
def generate_analysis(request, attempt_id: int):
    """
    Triggers the AI Inference Engine for a specific attempt.
    Returns the generated learning gap report.
    """
    # Ensure user owns the attempt or is admin (skipped for demo strictness, but good practice)
    # attempt = get_object_or_404(AssignmentAttempt, id=attempt_id, user=request.user)
    
    report = InferenceEngine.analyze_attempt(attempt_id)
    
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
    report = get_object_or_404(GapAnalysisReport, attempt_id=attempt_id)
    return {
        "student_name": report.student.username,
        "primary_gap": report.primary_gap,
        "secondary_gap": report.secondary_gap,
        "confidence_level": report.confidence_level,
        "recommendation": report.recommendation,
        "skill_traversal_path": report.skill_traversal_path,
        "generated_at": report.generated_at.strftime("%Y-%m-%d %H:%M:%S")
    }
