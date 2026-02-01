from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import Assignment, Question, AssignmentAttempt, QuizSubmission, OutputGuessSubmission, CodingSubmission

# Views serve templates; API handles submissions. All assignment views require login.

@login_required
def start_view(request):
    return render(request, 'assignments/start.html')

@login_required
def quiz_view(request, attempt_id):
    attempt = get_object_or_404(AssignmentAttempt, id=attempt_id, user=request.user)
    # Get all quiz questions for this assignment
    questions = Question.objects.filter(assignment=attempt.assignment, question_type='QUIZ')
    
    # Simple Navigation Logic:
    # Check submissions for this attempt. 
    # Find first question ID not in submissions?
    # This logic belongs in a Service, but here for View simplicity.
    submitted_ids = QuizSubmission.objects.filter(attempt=attempt).values_list('question_id', flat=True)
    next_q = questions.exclude(id__in=submitted_ids).first()
    
    if not next_q:
        # No more quiz questions, go to Logic
        return redirect('assignments:output_guess', attempt_id=attempt_id)
        
    return render(request, 'assignments/quiz.html', {
        'question': next_q.quiz_data,
        'question_id': next_q.id,
        'question_number': 1,
        'total_questions': questions.count(),
        'attempt_id': attempt_id,
        'next_url': reverse('assignments:quiz', args=[attempt_id])
    })

@login_required
def output_guess_view(request, attempt_id):
    attempt = get_object_or_404(AssignmentAttempt, id=attempt_id, user=request.user)
    questions = Question.objects.filter(assignment=attempt.assignment, question_type='OUTPUT')
    
    submitted_ids = OutputGuessSubmission.objects.filter(attempt=attempt).values_list('question_id', flat=True)
    next_q = questions.exclude(id__in=submitted_ids).first()
    
    if not next_q:
        return redirect('assignments:coding', attempt_id=attempt_id)
        
    return render(request, 'assignments/output_guess.html', {
        'question': next_q.output_data,
        'question_id': next_q.id,
        'attempt_id': attempt_id,
        'next_url': reverse('assignments:output_guess', args=[attempt_id])
    })

@login_required
def coding_view(request, attempt_id):
    attempt = get_object_or_404(AssignmentAttempt, id=attempt_id, user=request.user)
    questions = Question.objects.filter(assignment=attempt.assignment, question_type='CODE')
    
    submitted_ids = CodingSubmission.objects.filter(attempt=attempt).values_list('question_id', flat=True)
    next_q = questions.exclude(id__in=submitted_ids).first()
    
    if not next_q:
        return redirect('assignments:summary', attempt_id=attempt_id)
        
    return render(request, 'assignments/coding.html', {
        'question': next_q.coding_data,
        'question_id': next_q.id,
        'attempt_id': attempt_id,
        'complexity_rank_label': "Medium",
        'next_url': reverse('assignments:coding', args=[attempt_id])
    })

@login_required
def summary_view(request, attempt_id):
    attempt = get_object_or_404(AssignmentAttempt, id=attempt_id, user=request.user)
    from assignments.services.submission_service import SubmissionService
    attempt = SubmissionService.finalize_attempt(attempt_id)
    return render(request, 'assignments/summary.html', {'attempt': attempt})
