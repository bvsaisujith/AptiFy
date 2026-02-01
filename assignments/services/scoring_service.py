from django.db.models import Avg
from assignments.models import CodingSubmission, Question

class ScoringService:
    @staticmethod
    def calculate_quiz_score(correct_count: int, total_count: int) -> float:
        """
        Concept Score = (Correct Answers / Total Questions) * 100
        """
        if total_count == 0:
            return 0.0
        return (correct_count / total_count) * 100.0

    @staticmethod
    def calculate_logic_score(correct_predictions: int, total_questions: int) -> float:
        """
        Logic Score = (Correct Output Predictions / Total Output Questions) * 100
        """
        if total_questions == 0:
            return 0.0
        return (correct_predictions / total_questions) * 100.0

    @staticmethod
    def calculate_coding_score(submission: CodingSubmission, question_id: int) -> dict:
        """
        Calculate strict Relative Benchmark Score.
        Returns detailed dictionary of components.
        """
        # STEP 1: Filter Valid Submissions
        if not submission.code_runs:
            return {
                "correctness_score": 0.0,
                "time_score": 0.0,
                "optimality_score": 0.0,
                "final_score": 0.0,
                "benchmark_avg_time": 0.0,
                "benchmark_avg_complexity": 0.0,
                "tag": "Execution Failed"
            }

        # STEP 2: Calculate Benchmarks
        # Valid submissions are those where code_runs=True
        valid_submissions = CodingSubmission.objects.filter(
            question_id=question_id,
            code_runs=True
        ).exclude(id=submission.id) # Should we exclude current? The prompt says "Average of all valid submissions". 
        # Usually "all" includes the current one to establish the universe.
        # "Average of all submissions acts as baseline". Let's include current if saved, but it might not be saved yet?
        # If not saved, we can't query it. If saved, we query it.
        # Let's query all valid including this one if it's in DB, or append values if not.
        # Since we are calling this likely BEFORE or AFTER save? 
        # Usually scoring happens before final save or updates it. 
        # Let's assume we fetch averages of *others* + *current* to be mathematically strict "all".
        
        # However, for stability, often benchmarks are periodic. But prompt implies dynamic.
        stats = CodingSubmission.objects.filter(question_id=question_id, code_runs=True).aggregate(
            avg_time=Avg('execution_time_ms'),
            avg_complexity=Avg('complexity_rank')
        )
        
        # If this is the very first submission, stats will be None or just this one.
        # Ensure current values are part of the average if they aren't in DB yet?
        # Using a simplistic approach: Use DB stats. If None (first sub), use current as baseline.
        
        avg_time = stats['avg_time']
        avg_complexity = stats['avg_complexity']
        
        user_time = submission.execution_time_ms if submission.execution_time_ms is not None else 0.0
        user_complexity = submission.complexity_rank
        
        if avg_time is None:
            avg_time = user_time
        elif submission.id is None: # Not in DB yet
             # Re-calculate average manually if strict "all" needed
             count = CodingSubmission.objects.filter(question_id=question_id, code_runs=True).count()
             total_time = (avg_time * count) + user_time
             avg_time = total_time / (count + 1)
             
        if avg_complexity is None:
            avg_complexity = float(user_complexity)
        elif submission.id is None:
             count = CodingSubmission.objects.filter(question_id=question_id, code_runs=True).count()
             total_comp = (avg_complexity * count) + user_complexity
             avg_complexity = total_comp / (count + 1)

        # STEP 3: Correctness Score (50%)
        passed_pct = submission.testcases_passed_percentage
        correctness_score = 0.0
        
        if passed_pct == 100:
            correctness_score = 50.0
        elif passed_pct >= 50:
            # Scale linearly 25-40 for partial passes
            fraction = (passed_pct - 50) / 50.0
            correctness_score = 25 + (fraction * 15)
        else:
            # Compiles but wrong: 10-20
            fraction = passed_pct / 50.0
            correctness_score = 10 + (fraction * 10)
            
        if correctness_score == 0:
            return {
                "correctness_score": 0.0,
                "time_score": 0.0,
                "optimality_score": 0.0,
                "final_score": 0.0,
                "benchmark_avg_time": avg_time,
                "benchmark_avg_complexity": avg_complexity,
                "tag": "Needs practice"
            }

        # STEP 4: Time Performance Score (25%)
        # BASELINE 15
        time_score = 15.0
        if avg_time > 0:
            diff_factor = ((avg_time - user_time) / avg_time) * 10
            time_score = 15 + diff_factor
        
        # Clamp 0-25
        time_score = max(0.0, min(25.0, time_score))

        # STEP 5: Optimality Score (25%)
        # BASELINE 15
        optimal_score = 15.0
        # Lower rank is better.
        # Formula: 15 + ((avg_complexity - user_complexity) * 5)
        # If user (1) < avg (3) -> 15 + (2*5) = 25. High score for low complexity. Correct.
        diff_val = (avg_complexity - user_complexity) * 5
        optimal_score = 15 + diff_val
        
        # Clamp 0-25
        optimal_score = max(0.0, min(25.0, optimal_score))

        # STEP 6: Final Score
        final_score = correctness_score + time_score + optimal_score
        
        # Intelligence Tags
        tag = "Participant"
        # Heuristics provided:
        # if correctness high and time low: tag = "Needs practice"
        # if fast but low optimality: tag = "Needs algorithm learning"
        # if optimal but slow: tag = "Strong thinker, needs speed"
        # if all high: tag = "Industry-ready"
        
        # Define "High" and "Low" thresholds strictly?
        # Correctness Max 50. Time Max 25. Opt Max 25.
        
        c_high = correctness_score >= 40 
        t_high = time_score >= 20
        o_high = optimal_score >= 20
        
        t_low = time_score < 15 # Below baseline
        o_low = optimal_score < 15 # Below baseline
        
        if c_high and t_high and o_high:
            tag = "Industry-ready"
        elif c_high and t_low:
            tag = "Needs practice" # "Correctness high and time low"
        elif t_high and o_low:
            tag = "Needs algorithm learning" # "Fast but low optimality"
        elif o_high and t_low:
             tag = "Strong thinker, needs speed" # "Optimal but slow"
        
        return {
            "correctness_score": round(correctness_score, 2),
            "time_score": round(time_score, 2),
            "optimality_score": round(optimal_score, 2),
            "final_score": round(final_score, 2),
            "benchmark_avg_time": round(avg_time, 2),
            "benchmark_avg_complexity": round(avg_complexity, 2),
            "tag": tag
        }
