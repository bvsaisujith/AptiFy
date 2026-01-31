from django.shortcuts import render, get_object_or_404, redirect
from .models import GapAnalysisReport
from assignments.models import AssignmentAttempt
from .services.inference_engine import InferenceEngine

def report_view(request, attempt_id):
    # Try to get existing report
    report = GapAnalysisReport.objects.filter(attempt_id=attempt_id).first()
    
    if not report:
        # If not exists, should we generate it on the fly?
        # Ideally, use POST API. But for seamless View navigation:
        try:
            report = InferenceEngine.analyze_attempt(attempt_id)
        except Exception as e:
            # Handle error
            return render(request, 'assignments/base.html', {'error': str(e)})

    return render(request, 'analysis/report.html', {'report': report})
