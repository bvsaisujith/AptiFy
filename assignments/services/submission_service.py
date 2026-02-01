from django.utils import timezone
from django.db import transaction
from django.db.models import Avg
from assignments.models import (
    AssignmentAttempt, Question, QuizSubmission, OutputGuessSubmission, CodingSubmission,
    QuizQuestion, OutputGuessQuestion
)
from assignments.services.scoring_service import ScoringService

class SubmissionService:
    
    @staticmethod
    def start_assignment(user, assignment_id):
        prior_attempts = AssignmentAttempt.objects.filter(user=user, assignment_id=assignment_id).count()
        attempt = AssignmentAttempt.objects.create(
            user=user,
            assignment_id=assignment_id,
            module2_data={
                "attempt_count": prior_attempts + 1,
                "timestamp": timezone.now().isoformat()
            }
        )
        return attempt

    @staticmethod
    def submit_quiz_answer(attempt_id, question_id, selected_option_id, time_taken_seconds=None):
        question = QuizQuestion.objects.get(question_id=question_id)
        is_correct = (selected_option_id == question.correct_option_id)
        
        QuizSubmission.objects.create(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_option_id=selected_option_id,
            is_correct=is_correct,
            time_taken_seconds=time_taken_seconds or 0
        )
        return is_correct

    @staticmethod
    def submit_output_guess(attempt_id, question_id, predicted_output, time_taken_seconds=None):
        question = OutputGuessQuestion.objects.get(question_id=question_id)
        # Normalize strings for comparison (strip whitespace)
        is_correct = (predicted_output.strip() == question.correct_output.strip())
        
        OutputGuessSubmission.objects.create(
            attempt_id=attempt_id,
            question_id=question_id,
            predicted_output=predicted_output,
            is_correct=is_correct,
            time_taken_seconds=time_taken_seconds or 0
        )
        return is_correct

    @staticmethod
    def submit_code(attempt_id, question_id, code, time_taken, complexity_rank, testcases_passed_percentage, code_runs, language="python"):
        # Create submission with raw metrics
        time_taken_seconds = (time_taken / 1000) if time_taken else 0
        submission = CodingSubmission(
            attempt_id=attempt_id,
            question_id=question_id,
            submitted_code=code,
            time_taken_seconds=time_taken_seconds,
            
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
        quiz_submissions = QuizSubmission.objects.filter(attempt=attempt)
        quiz_total = quiz_submissions.count()
        quiz_correct = quiz_submissions.filter(is_correct=True).count()
        attempt.concept_score = ScoringService.calculate_quiz_score(quiz_correct, quiz_total)

        incorrect_concepts = []
        time_taken_per_question = []
        for submission in quiz_submissions.select_related("question"):
            time_taken_per_question.append({
                "question_id": submission.question_id,
                "time_taken_seconds": submission.time_taken_seconds
            })
            if not submission.is_correct:
                concept_tag = submission.question.concept_tag or submission.question.sub_skill or "General"
                incorrect_concepts.append({
                    "question_id": submission.question_id,
                    "concept_tag": concept_tag,
                    "difficulty": submission.question.difficulty
                })
        
        # 2. Calculate Logic Score
        logic_submissions = OutputGuessSubmission.objects.filter(attempt=attempt)
        logic_total = logic_submissions.count()
        logic_correct = logic_submissions.filter(is_correct=True).count()
        attempt.logic_score = ScoringService.calculate_logic_score(logic_correct, logic_total)

        wrong_execution_patterns = []
        repeated_logic_errors = []
        logic_time_taken = []
        sub_skill_errors = {}
        for submission in logic_submissions.select_related("question"):
            logic_time_taken.append({
                "question_id": submission.question_id,
                "time_taken_seconds": submission.time_taken_seconds
            })
            if not submission.is_correct:
                wrong_execution_patterns.append({
                    "question_id": submission.question_id,
                    "sub_skill": submission.question.sub_skill,
                    "difficulty": submission.question.difficulty
                })
                key = submission.question.sub_skill or "General"
                sub_skill_errors[key] = sub_skill_errors.get(key, 0) + 1

        for sub_skill, count in sub_skill_errors.items():
            if count > 1:
                repeated_logic_errors.append({"sub_skill": sub_skill, "count": count})
        
        # 3. Calculate Execution Score
        # Average of all coding problems? Or Sum?
        # Requires clarification. Usually "Execution Score" is 0-100.
        # Let's average the percentage of the coding problems.
        coding_submissions = CodingSubmission.objects.filter(attempt=attempt)
        if coding_submissions.exists():
            # coding_submission.total_score is out of 100
            avg_code_score = coding_submissions.aggregate(Avg('total_score'))['total_score__avg']
            attempt.execution_score = avg_code_score
        else:
            attempt.execution_score = 0.0

        time_metrics = []
        complexity_rank = []
        for submission in coding_submissions:
            time_metrics.append({
                "question_id": submission.question_id,
                "execution_time_ms": submission.execution_time_ms,
                "time_taken_seconds": submission.time_taken_seconds
            })
            complexity_rank.append({
                "question_id": submission.question_id,
                "rank": submission.complexity_rank
            })
            
        attempt.completed_at = timezone.now()
        attempt.module2_data = {
            **(attempt.module2_data or {}),
            "concept_score": attempt.concept_score,
            "logic_score": attempt.logic_score,
            "execution_score": attempt.execution_score,
            "incorrect_concepts": incorrect_concepts,
            "time_taken_per_question": time_taken_per_question,
            "wrong_execution_patterns": wrong_execution_patterns,
            "repeated_logic_errors": repeated_logic_errors,
            "logic_time_taken": logic_time_taken,
            "time_metrics": time_metrics,
            "complexity_rank": complexity_rank,
            "attempt_history": attempt.module2_data.get("attempt_count", 1),
            "timestamp": attempt.completed_at.isoformat()
        }
        attempt.save()
        return attempt
