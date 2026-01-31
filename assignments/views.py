from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import Assignment, Question, AssignmentAttempt

# Simple Views to serve templates. Authorization handled by templates or API calls.
# Note: For production, we'd add @login_required. For strict Agent demo, I'll add it but ensure mock user works if needed.

def start_view(request):
    return render(request, 'assignments/start.html')

def quiz_view(request, attempt_id):
    # Fetch a quiz question. For demo, simplified: Get first Quiz Question.
    # Logic: Find attempt, find next unanswered question.
    attempt = get_object_or_404(AssignmentAttempt, id=attempt_id)
    # Get all quiz questions for this assignment
    questions = Question.objects.filter(assignment=attempt.assignment, question_type='QUIZ')
    
    # Simple Navigation Logic:
    # Check submissions for this attempt. 
    # Find first question ID not in submissions?
    # This logic belongs in a Service, but here for View simplicity.
    submitted_ids = attempt.submissions.values_list('question_id', flat=True)
    next_q = questions.exclude(id__in=submitted_ids).first()
    
    if not next_q:
        # No more quiz questions, go to Logic
        return redirect('assignments:output_guess', attempt_id=attempt_id)
        
    return render(request, 'assignments/quiz.html', {
        'question': next_q.quiz_data, # specific model
        'question_number': 1, # Todo: calc index
        'total_questions': questions.count(),
        'attempt_id': attempt_id,
        'next_url': reverse('assignments:quiz', args=[attempt_id]) # Recursive route until done
    })

def output_guess_view(request, attempt_id):
    attempt = get_object_or_404(AssignmentAttempt, id=attempt_id)
    questions = Question.objects.filter(assignment=attempt.assignment, question_type='OUTPUT')
    
    submitted_ids = attempt.submissions.values_list('question_id', flat=True)
    next_q = questions.exclude(id__in=submitted_ids).first()
    
    if not next_q:
        return redirect('assignments:coding', attempt_id=attempt_id)
        
    return render(request, 'assignments/output_guess.html', {
        'question': next_q.output_data,
        'attempt_id': attempt_id,
        'next_url': reverse('assignments:output_guess', args=[attempt_id])
    })

def coding_view(request, attempt_id):
    attempt = get_object_or_404(AssignmentAttempt, id=attempt_id)
    questions = Question.objects.filter(assignment=attempt.assignment, question_type='CODE')
    
    submitted_ids = attempt.submissions.values_list('question_id', flat=True)
    next_q = questions.exclude(id__in=submitted_ids).first()
    
    if not next_q:
        return redirect('assignments:summary', attempt_id=attempt_id)
        
    return render(request, 'assignments/coding.html', {
        'question': next_q.coding_data,
        'attempt_id': attempt_id,
        'complexity_rank_label': "Medium", # Placeholder
        'next_url': reverse('assignments:coding', args=[attempt_id])
    })

def summary_view(request, attempt_id):
    attempt = get_object_or_404(AssignmentAttempt, id=attempt_id)
    return render(request, 'assignments/summary.html', {'attempt': attempt})
