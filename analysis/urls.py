from django.urls import path
from . import views

app_name = 'analysis'

urlpatterns = [
    path('report/<int:attempt_id>/', views.report_view, name='report'),
]
