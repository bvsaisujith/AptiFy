from assignments.models import AssignmentAttempt
from analysis.models import GapAnalysisReport, SkillAnalysis

class InferenceEngine:
    @staticmethod
    def analyze_attempt(attempt_id):
        """
        Main entry point for AI Analysis.
        Consumes scores, identifies gaps, traverses skill graph, and generates report.
        """
        attempt = AssignmentAttempt.objects.get(id=attempt_id)
        
        # 1. Normalize Scores (0-100)
        # Assuming scores are already 0-100 in database.
        quiz_score = attempt.concept_score
        logic_score = attempt.logic_score
        code_score = attempt.execution_score
        
        # 2. Rule-Based Inference (The 5 Rules)
        primary_gap = "Unknown"
        secondary_gap = ""
        recommendation = "Practice more."
        confidence = 0.0
        
        # Thresholds (High >= 60, Low < 60) - Heuristic for analysis
        HIGH = 60.0
        
        is_quiz_high = quiz_score >= HIGH
        is_logic_high = logic_score >= HIGH
        is_code_high = code_score >= HIGH
        
        if is_quiz_high and not is_code_high:
            # Rule 1: High Quiz + Low Coding
            primary_gap = "Execution Gap"
            secondary_gap = "Application of Theory"
            recommendation = "You understand the concepts but struggle to apply them. Focus on writing more code from scratch rather than just reading."
            confidence = 85.0
            
        elif is_logic_high and not is_code_high:
            # Rule 2: High Logic + Low Coding
            primary_gap = "Syntax/Implementation Gap"
            secondary_gap = "Language Constructs"
            recommendation = "Your logic is sound, but you struggle with the language syntax. Practice coding simple problems to build muscle memory."
            confidence = 80.0
            
        elif not is_quiz_high and is_code_high:
            # Rule 3: Low Quiz + High Coding
            primary_gap = "Conceptual Gap"
            secondary_gap = "Theoretical Foundation"
            recommendation = "You are a practical learner but lack theoretical depth. Review the core concepts to ensure you aren't just memorizing patterns."
            confidence = 85.0
            
        elif not is_logic_high and not is_code_high:
            # Rule 4: Low Logic + Low Coding (Foundational)
            primary_gap = "Foundational Logic Gap"
            secondary_gap = "Algorithmic Thinking"
            recommendation = "You are struggling with both dry-runs and coding. Start with flowcharting and dry-running code on paper before typing."
            confidence = 90.0
            
        elif is_quiz_high and is_logic_high and is_code_high:
            # Rule 5: High All
            primary_gap = "None"
            secondary_gap = "Optimization"
            recommendation = "You are industry-ready! Focus on advanced optimization and system design."
            confidence = 95.0
        else:
            # Mixed/Edge cases
            primary_gap = "Mixed Gap"
            secondary_gap = "General Practice"
            recommendation = "Your performance is varied. identifying specific weak spots in sub-skills is recommended."
            confidence = 60.0

        # 3. Create Report
        report, created = GapAnalysisReport.objects.update_or_create(
            attempt=attempt,
            defaults={
                'student': attempt.user,
                'primary_gap': primary_gap,
                'secondary_gap': secondary_gap,
                'confidence_level': confidence,
                'recommendation': recommendation,
                'skill_traversal_path': ["Root Analysis", primary_gap] # Placeholder for full graph
            }
        )
        
        # 4. Save Skill Analysis (Mock for now)
        SkillAnalysis.objects.create(report=report, skill_name="Python Syntax", status='STRONG' if is_code_high else 'WEAK')
        SkillAnalysis.objects.create(report=report, skill_name="Logic Building", status='STRONG' if is_logic_high else 'WEAK')
        
        return report
