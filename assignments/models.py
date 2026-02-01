from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _

class Assignment(models.Model):
    """
    Represents a complete assignment containing multiple sections/questions.
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Skill(models.Model):
    """
    Represents a broad skill (e.g., 'Python', 'Algorithms').
    """
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class Question(models.Model):
    """
    Base model for all question types.
    """
    class Difficulty(models.TextChoices):
        EASY = 'EASY', _('Easy')
        MEDIUM = 'MEDIUM', _('Medium')
        HARD = 'HARD', _('Hard')

    class QuestionType(models.TextChoices):
        QUIZ = 'QUIZ', _('Quiz (MCQ)')
        OUTPUT = 'OUTPUT', _('Guess Output')
        CODE = 'CODE', _('Coding Problem')

    assignment = models.ForeignKey(Assignment, related_name='questions', on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True)
    sub_skill = models.CharField(max_length=100, blank=True)
    concept_tag = models.CharField(max_length=120, blank=True)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    question_type = models.CharField(max_length=10, choices=QuestionType.choices)
    
    # Common fields
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_question_type_display()} - {self.id}"

class QuizQuestion(models.Model):
    """
    Specific data for MCQ questions.
    """
    question = models.OneToOneField(Question, related_name='quiz_data', on_delete=models.CASCADE)
    text = models.TextField()
    options = models.JSONField(help_text="Format: [{'id': 'a', 'text': 'Option A'}, ...]")
    correct_option_id = models.CharField(max_length=50)

    def __str__(self):
        return f"Quiz: {self.text[:50]}"

class OutputGuessQuestion(models.Model):
    """
    Specific data for 'Guess the Output' questions.
    """
    question = models.OneToOneField(Question, related_name='output_data', on_delete=models.CASCADE)
    code_snippet = models.TextField()
    correct_output = models.TextField()

    def __str__(self):
        return f"Output Guess - {self.question.id}"

class CodingQuestion(models.Model):
    """
    Specific data for Coding problems.
    """
    question = models.OneToOneField(Question, related_name='coding_data', on_delete=models.CASCADE)
    problem_statement = models.TextField()
    constraints = models.TextField(blank=True)
    # Test cases: [{'input': '...', 'output': '...', 'hidden': boolean}]
    test_cases = models.JSONField()
    
    def __str__(self):
        return f"Coding - {self.question.id}"

class AssignmentAttempt(models.Model):
    """
    Tracks a student's attempt at an assignment.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Aggregated Scores
    concept_score = models.FloatField(default=0.0) # From Quiz
    logic_score = models.FloatField(default=0.0)   # From Output Guess
    execution_score = models.FloatField(default=0.0) # From Coding
    
    # Metadata
    error_patterns = models.JSONField(default=list, blank=True)
    module2_data = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.user} - {self.assignment} - {self.started_at}"

class Submission(models.Model):
    """
    Base model for individual question submissions.
    """
    attempt = models.ForeignKey(AssignmentAttempt, related_name='%(class)s_submissions', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    time_taken_seconds = models.FloatField(help_text="Time taken to answer this specific question")

    class Meta:
        abstract = True

class QuizSubmission(Submission):
    selected_option_id = models.CharField(max_length=50)
    is_correct = models.BooleanField()

class OutputGuessSubmission(Submission):
    predicted_output = models.TextField()
    is_correct = models.BooleanField()

class CodingSubmission(Submission):
    submitted_code = models.TextField()
    
    # Execution Metrics
    is_correct = models.BooleanField(default=False)
    passed_test_cases = models.IntegerField(default=0)
    total_test_cases = models.IntegerField(default=0)
    
    # Scores (Component wise)
    correctness_score = models.FloatField(default=0.0) # 50% max
    time_perf_score = models.FloatField(default=0.0)   # 25% max
    optimality_score = models.FloatField(default=0.0)  # 25% max
    
    total_score = models.FloatField(default=0.0) # Sum of above
    
    # Metadata
    execution_time_ms = models.FloatField(null=True)
    memory_usage_kb = models.FloatField(null=True)
    complexity_analysis = models.CharField(max_length=50, blank=True) # e.g. O(n)
    
    # Strict metrics for Relative Scoring
    complexity_rank = models.IntegerField(default=3, help_text="1=O(n), 2=O(nlogn), 3=O(n^2), 4=O(n^3)")
    testcases_passed_percentage = models.FloatField(default=0.0)
    code_runs = models.BooleanField(default=False)

