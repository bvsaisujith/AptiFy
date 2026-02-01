from typing import List, Optional
from ninja import Router, Schema
from ninja.security import django_auth
from django.shortcuts import get_object_or_404
from assignments.models import Assignment, AssignmentAttempt, Question, Skill
from assignments.services.submission_service import SubmissionService

router = Router()

# SCHEMAS

class AssignmentListItemSchema(Schema):
    id: int
    title: str
    description: str

class AttemptListItemSchema(Schema):
    id: int
    assignment_id: int
    assignment_title: str
    started_at: str
    completed_at: Optional[str]
    concept_score: float
    logic_score: float
    execution_score: float

class SkillListItemSchema(Schema):
    id: int
    name: str

class StartAssignmentSchema(Schema):
    assignment_id: int

class QuizSubmitSchema(Schema):
    attempt_id: int
    question_id: int
    selected_option_id: str
    time_taken_seconds: Optional[float] = None

class OutputSubmitSchema(Schema):
    attempt_id: int
    question_id: int
    predicted_output: str
    time_taken_seconds: Optional[float] = None

class CodeSubmitSchema(Schema):
    attempt_id: int
    question_id: int
    code: str
    execution_time: float # ms
    complexity_rank: int # 1-4
    testcases_passed_percentage: float
    code_runs: bool
    language: str = "python"

class AttemptSummarySchema(Schema):
    id: int
    user_id: int
    assignment_id: int
    started_at: str
    completed_at: Optional[str]
    concept_score: float
    logic_score: float
    execution_score: float

# ENDPOINTS (static paths before dynamic {attempt_id})

@router.get("/list", auth=django_auth, response=List[AssignmentListItemSchema])
def list_assignments(request):
    """List all assignments available to start."""
    assignments = Assignment.objects.all().order_by("id")
    return [{"id": a.id, "title": a.title, "description": a.description or ""} for a in assignments]

@router.get("/attempts", auth=django_auth, response=List[AttemptListItemSchema])
def list_attempts(request):
    """List current user's assignment attempts (latest first)."""
    attempts = AssignmentAttempt.objects.filter(user=request.user).select_related("assignment").order_by("-started_at")
    return [
        {
            "id": a.id,
            "assignment_id": a.assignment_id,
            "assignment_title": a.assignment.title,
            "started_at": str(a.started_at),
            "completed_at": str(a.completed_at) if a.completed_at else None,
            "concept_score": a.concept_score,
            "logic_score": a.logic_score,
            "execution_score": a.execution_score,
        }
        for a in attempts
    ]

@router.get("/skills", auth=django_auth, response=List[SkillListItemSchema])
def list_skills(request):
    """List all skills (for profile / assignment context)."""
    skills = Skill.objects.all().order_by("name")
    return [{"id": s.id, "name": s.name} for s in skills]

@router.post("/start", auth=django_auth, response=AttemptSummarySchema)
def start_assignment(request, data: StartAssignmentSchema):
    get_object_or_404(Assignment, id=data.assignment_id)
    attempt = SubmissionService.start_assignment(request.user, data.assignment_id)
    return {
        "id": attempt.id,
        "user_id": attempt.user.id,
        "assignment_id": attempt.assignment.id,
        "started_at": str(attempt.started_at),
        "completed_at": str(attempt.completed_at) if attempt.completed_at else None,
        "concept_score": attempt.concept_score,
        "logic_score": attempt.logic_score,
        "execution_score": attempt.execution_score,
    }

@router.post("/quiz/submit", auth=django_auth)
def submit_quiz_answer(request, data: QuizSubmitSchema):
    get_object_or_404(AssignmentAttempt, id=data.attempt_id, user=request.user)
    is_correct = SubmissionService.submit_quiz_answer(
        data.attempt_id, data.question_id, data.selected_option_id, data.time_taken_seconds
    )
    return {"success": True, "is_correct": is_correct}

@router.post("/output/submit", auth=django_auth)
def submit_output_guess(request, data: OutputSubmitSchema):
    get_object_or_404(AssignmentAttempt, id=data.attempt_id, user=request.user)
    is_correct = SubmissionService.submit_output_guess(
        data.attempt_id, data.question_id, data.predicted_output, data.time_taken_seconds
    )
    return {"success": True, "is_correct": is_correct}

@router.post("/code/submit", auth=django_auth)
def submit_code(request, data: CodeSubmitSchema):
    get_object_or_404(AssignmentAttempt, id=data.attempt_id, user=request.user)
    submission = SubmissionService.submit_code(
        data.attempt_id, 
        data.question_id, 
        data.code, 
        data.execution_time, 
        data.complexity_rank,
        data.testcases_passed_percentage,
        data.code_runs,
        data.language
    )
    return {
        "success": True, 
        "submission_id": submission.id,
        "is_correct": submission.is_correct,
        "total_score": submission.total_score,
        "feedback": {
            "correctness": submission.correctness_score,
            "time_score": submission.time_perf_score,
            "optimality": submission.optimality_score,
            "tag": getattr(submission, 'tag', "Evaluated")
        }
    }

@router.get("/{attempt_id}/summary", auth=django_auth, response=AttemptSummarySchema)
def get_attempt_summary(request, attempt_id: int):
    from django.shortcuts import get_object_or_404
    attempt = get_object_or_404(AssignmentAttempt, id=attempt_id, user=request.user)
    attempt = SubmissionService.finalize_attempt(attempt_id)
    return {
        "id": attempt.id,
        "user_id": attempt.user.id,
        "assignment_id": attempt.assignment.id,
        "started_at": str(attempt.started_at),
        "completed_at": str(attempt.completed_at) if attempt.completed_at else None,
        "concept_score": attempt.concept_score,
        "logic_score": attempt.logic_score,
        "execution_score": attempt.execution_score,
    }
