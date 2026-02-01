"""
URL configuration for aptify project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from aptify.api import api
from users.views import (
    LandingView, IndexView, LoginView, DashboardView,
    GoalListView, GoalCreateView, GoalUpdateView, GoalDeleteView,
    CourseListView, CourseCreateView, CourseDetailView, CourseUpdateView, CourseDeleteView,
    CourseResourceCreateView, CourseResourceUpdateView, CourseResourceDeleteView
)
from django.views.generic import TemplateView

urlpatterns = [
    # Landing page (public)
    path('', LandingView.as_view(), name='landing'),
    path('index/', IndexView.as_view(), name='index'),
    path('login/', LoginView.as_view(), name='login'),
    
    # Dashboard (protected)
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),
    path('intelligence/', TemplateView.as_view(template_name='intelligence.html'), name='intelligence'),
    path('settings/', TemplateView.as_view(template_name='settings.html'), name='settings'),
    
    # Goals management (protected)
    path('goals/', GoalListView.as_view(), name='goal-list'),
    path('goals/create/', GoalCreateView.as_view(), name='goal-create'),
    path('goals/<int:pk>/edit/', GoalUpdateView.as_view(), name='goal-update'),
    path('goals/<int:pk>/delete/', GoalDeleteView.as_view(), name='goal-delete'),
    
    # Courses management (protected)
    path('courses/', CourseListView.as_view(), name='course-list'),
    path('courses/create/', CourseCreateView.as_view(), name='course-create'),
    path('courses/<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
    path('courses/<int:pk>/edit/', CourseUpdateView.as_view(), name='course-update'),
    path('courses/<int:pk>/delete/', CourseDeleteView.as_view(), name='course-delete'),
    
    # Course Resources (protected)
    path('courses/<int:course_pk>/resources/add/', CourseResourceCreateView.as_view(), name='course-resource-create'),
    path('resources/<int:pk>/edit/', CourseResourceUpdateView.as_view(), name='course-resource-update'),
    path('resources/<int:pk>/delete/', CourseResourceDeleteView.as_view(), name='course-resource-delete'),
    
    # Allauth URLs (login, logout, signup, password reset, etc.)
    path('accounts/', include('allauth.urls')),
    
    # Admin
    path('aptify-admin/', admin.site.urls),
    
    # App URLs
    path('assignments/', include('assignments.urls')),
    path('analysis/', include('analysis.urls')),
    path('api/', api.urls),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
