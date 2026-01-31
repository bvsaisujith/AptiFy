from typing import List, Optional
from ninja import Router, Schema
from ninja.security import django_auth
from django.shortcuts import get_object_or_404
from assignments.models import AssignmentAttempt, Question
from assignments.services.submission_service import SubmissionService

router = Router()

# SCHEMAS

class StartAssignmentSchema(Schema):
    assignment_id: int

class QuizSubmitSchema(Schema):
    attempt_id: int
    question_id: int
    selected_option_id: str

class OutputSubmitSchema(Schema):
    attempt_id: int
    question_id: int
    predicted_output: str

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

# ENDPOINTS

@router.post("/start", auth=django_auth, response=AttemptSummarySchema)
def start_assignment(request, data: StartAssignmentSchema):
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
    is_correct = SubmissionService.submit_quiz_answer(
        data.attempt_id, data.question_id, data.selected_option_id
    )
    return {"success": True, "is_correct": is_correct}

@router.post("/output/submit", auth=django_auth)
def submit_output_guess(request, data: OutputSubmitSchema):
    is_correct = SubmissionService.submit_output_guess(
        data.attempt_id, data.question_id, data.predicted_output
    )
    return {"success": True, "is_correct": is_correct}

@router.post("/code/submit", auth=django_auth)
def submit_code(request, data: CodeSubmitSchema):
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
