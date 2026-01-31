from django.utils import timezone
from django.db import transaction
from assignments.models import (
    AssignmentAttempt, Question, QuizSubmission, OutputGuessSubmission, CodingSubmission,
    QuizQuestion, OutputGuessQuestion
)
from assignments.services.scoring_service import ScoringService

class SubmissionService:
    
    @staticmethod
    def start_assignment(user, assignment_id):
        attempt = AssignmentAttempt.objects.create(
            user=user,
            assignment_id=assignment_id
        )
        return attempt

    @staticmethod
    def submit_quiz_answer(attempt_id, question_id, selected_option_id):
        question = QuizQuestion.objects.get(question_id=question_id)
        is_correct = (selected_option_id == question.correct_option_id)
        
        Submission = QuizSubmission.objects.create(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_option_id=selected_option_id,
            is_correct=is_correct,
            time_taken_seconds=0 # Logic to tracking time per question needs frontend to send delta
        )
        return is_correct

    @staticmethod
    def submit_output_guess(attempt_id, question_id, predicted_output):
        question = OutputGuessQuestion.objects.get(question_id=question_id)
        # Normalize strings for comparison (strip whitespace)
        is_correct = (predicted_output.strip() == question.correct_output.strip())
        
        OutputGuessSubmission.objects.create(
            attempt_id=attempt_id,
            question_id=question_id,
            predicted_output=predicted_output,
            is_correct=is_correct,
            time_taken_seconds=0 # Placeholder
        )
        return is_correct

    @staticmethod
    def submit_code(attempt_id, question_id, code, time_taken, complexity_rank, testcases_passed_percentage, code_runs, language="python"):
        # Create submission with raw metrics
        submission = CodingSubmission(
            attempt_id=attempt_id,
            question_id=question_id,
            submitted_code=code,
            time_taken_seconds=time_taken,
            
            # Execution Metrics
            execution_time_ms=time_taken, # Assuming input is ms? User said "execution_time". DB has "time_taken_seconds". 
            # Prompt says "execution_time" in input. DB has `execution_time_ms` and `time_taken_seconds`.
            # Let's standardize: Input `execution_time` is in ms. `time_taken_seconds` is execution_time/1000.
            # But the models.py has `execution_time_ms` and `time_taken_seconds`.
            # Let's assume the API sends `execution_time` (ms).
            
            complexity_rank=complexity_rank,
            testcases_passed_percentage=testcases_passed_percentage,
            code_runs=code_runs,
            
            # Derived correctness (for simplified querying if needed, but widely we use score)
            is_correct=(testcases_passed_percentage == 100)
        )
        
        # Calculate Scores using strict service
        scores = ScoringService.calculate_coding_score(submission, question_id) 
        
        submission.correctness_score = scores["correctness_score"]
        submission.time_perf_score = scores["time_score"]
        submission.optimality_score = scores["optimality_score"]
        submission.total_score = scores["final_score"]
        
        # Determine strict pass/fail or tagging? 
        # The prompt asks for tagging in output, but maybe store it too? 
        # Tag is returned, maybe we can store it in metadata or just return it. 
        # Not explicitly asked to store tag in DB, but good for reporting.
        # Let's store it in complexity_analysis or a new field if needed. 
        # For now, just save scores.
        
        submission.save()
        
        # Attach the tag to the object temporarily for return (not saved to DB)
        submission.tag = scores["tag"]
        
        return submission

    @staticmethod
    def finalize_attempt(attempt_id):
        """
        Aggregates all submissions and updates the Attempt with final scores.
        """
        attempt = AssignmentAttempt.objects.get(id=attempt_id)
        
        # 1. Calculate Quiz Score
        quiz_submissions = attempt.submissions.instance_of(QuizSubmission)
        quiz_total = quiz_submissions.count()
        quiz_correct = quiz_submissions.filter(quizsubmission__is_correct=True).count()
        attempt.concept_score = ScoringService.calculate_quiz_score(quiz_correct, quiz_total)
        
        # 2. Calculate Logic Score
        logic_submissions = attempt.submissions.instance_of(OutputGuessSubmission)
        logic_total = logic_submissions.count()
        logic_correct = logic_submissions.filter(outputguesssubmission__is_correct=True).count()
        attempt.logic_score = ScoringService.calculate_logic_score(logic_correct, logic_total)
        
        # 3. Calculate Execution Score
        # Average of all coding problems? Or Sum?
        # Requires clarification. Usually "Execution Score" is 0-100.
        # Let's average the percentage of the coding problems.
        coding_submissions = attempt.submissions.instance_of(CodingSubmission)
        if coding_submissions.exists():
            # coding_submission.total_score is out of 100
            avg_code_score = coding_submissions.aggregate(Avg('codingsubmission__total_score'))['codingsubmission__total_score__avg']
            attempt.execution_score = avg_code_score
        else:
            attempt.execution_score = 0.0
            
        attempt.completed_at = timezone.now()
        attempt.save()
        return attempt
