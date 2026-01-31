from django.urls import path
from . import views

app_name = 'assignments'

urlpatterns = [
    path('', views.start_view, name='start'),
    path('quiz/<int:attempt_id>/', views.quiz_view, name='quiz'),
    path('output/<int:attempt_id>/', views.output_guess_view, name='output_guess'),
    path('code/<int:attempt_id>/', views.coding_view, name='coding'),
    path('summary/<int:attempt_id>/', views.summary_view, name='summary'),
]
