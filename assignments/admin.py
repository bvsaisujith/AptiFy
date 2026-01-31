from django.contrib import admin
from .models import (
    Assignment, Skill, Question, QuizQuestion, OutputGuessQuestion, CodingQuestion,
    AssignmentAttempt, QuizSubmission, OutputGuessSubmission, CodingSubmission
)

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')
    search_fields = ('title',)

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name',)

class QuizQuestionInline(admin.StackedInline):
    model = QuizQuestion
    extra = 1

class OutputGuessQuestionInline(admin.StackedInline):
    model = OutputGuessQuestion
    extra = 1

class CodingQuestionInline(admin.StackedInline):
    model = CodingQuestion
    extra = 1

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'assignment', 'question_type', 'difficulty', 'skill')
    list_filter = ('question_type', 'difficulty', 'skill')
    inlines = [QuizQuestionInline, OutputGuessQuestionInline, CodingQuestionInline]

@admin.register(AssignmentAttempt)
class AssignmentAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'assignment', 'started_at', 'completed_at', 'concept_score', 'logic_score', 'execution_score')
    list_filter = ('assignment', 'started_at')

# Registering specialized question models separately if needed, 
# though they are managed via QuestionAdmin inlines mostly.
admin.site.register(QuizQuestion)
admin.site.register(OutputGuessQuestion)
admin.site.register(CodingQuestion)

# Submissions
admin.site.register(QuizSubmission)
admin.site.register(OutputGuessSubmission)
admin.site.register(CodingSubmission)
