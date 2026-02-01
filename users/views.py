from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from users.models import Goal, Course, CourseResource, CourseEnrollment
from users.forms import GoalForm, GoalFilterForm, CourseForm, CourseResourceForm, CourseFilterForm


class LandingView(TemplateView):
    """Landing page - public entry point. Redirects to dashboard if logged in."""
    template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().get(request, *args, **kwargs)


class IndexView(TemplateView):
    """Entry gate - redirects based on auth status via JavaScript"""
    template_name = 'index.html'


class LoginView(TemplateView):
    """Public login page"""
    template_name = 'login.html'


class DashboardView(LoginRequiredMixin, TemplateView):
    """Protected dashboard page - requires authentication"""
    template_name = 'dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get user's goals for the dashboard
        user_goals = Goal.objects.filter(user=self.request.user)
        context['total_goals'] = user_goals.count()
        context['completed_goals'] = user_goals.filter(status='completed').count()
        context['active_goals'] = user_goals.filter(status__in=['not_started', 'in_progress']).count()
        context['recent_goals'] = user_goals[:3]  # Show 3 most recent goals
        return context


class GoalListView(LoginRequiredMixin, ListView):
    """Display user's goals with filtering and sorting"""
    model = Goal
    template_name = 'goals/goal_list.html'
    context_object_name = 'goals'
    paginate_by = 10
    
    def get_queryset(self):
        # Filter goals for current user
        queryset = Goal.objects.filter(user=self.request.user)
        
        # Apply status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Apply sorting
        sort = self.request.GET.get('sort', 'deadline')
        queryset = queryset.order_by(sort)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = GoalFilterForm(self.request.GET)
        return context


class GoalCreateView(LoginRequiredMixin, CreateView):
    """Create a new goal"""
    model = Goal
    form_class = GoalForm
    template_name = 'goals/goal_form.html'
    success_url = reverse_lazy('goal-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Goal created successfully!')
        return super().form_valid(form)


class GoalUpdateView(LoginRequiredMixin, UpdateView):
    """Edit an existing goal"""
    model = Goal
    form_class = GoalForm
    template_name = 'goals/goal_form.html'
    success_url = reverse_lazy('goal-list')
    
    def get_queryset(self):
        # Only allow user to edit their own goals
        return Goal.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        # Update completed_at timestamp when goal is marked as completed
        if form.instance.status == 'completed' and not form.instance.completed_at:
            form.instance.completed_at = timezone.now()
        messages.success(self.request, 'Goal updated successfully!')
        return super().form_valid(form)


class GoalDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a goal"""
    model = Goal
    template_name = 'goals/goal_confirm_delete.html'
    success_url = reverse_lazy('goal-list')
    
    def get_queryset(self):
        # Only allow user to delete their own goals
        return Goal.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Goal deleted successfully!')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# COURSE VIEWS
# ============================================================================

class CourseListView(LoginRequiredMixin, ListView):
    """Display all available courses on the platform with filtering and sorting"""
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 12
    
    def get_queryset(self):
        # Show all published courses available on the platform
        queryset = Course.objects.filter(status='published')
        
        # Apply category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__icontains=category)
        
        # Apply level filter
        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(level=level)
        
        # Apply sorting
        sort = self.request.GET.get('sort', '-created_at')
        queryset = queryset.order_by(sort)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = CourseFilterForm(self.request.GET)
        # Get user's created courses (for management)
        user_courses = Course.objects.filter(user=self.request.user).count()
        context['user_courses_created'] = user_courses
        # Get enrollment stats
        user_enrollments = CourseEnrollment.objects.filter(user=self.request.user)
        context['total_courses'] = user_enrollments.count()
        context['completed_courses'] = user_enrollments.filter(status='completed').count()
        context['in_progress_courses'] = user_enrollments.filter(status='in_progress').count()
        return context


class CourseCreateView(LoginRequiredMixin, CreateView):
    """Create a new course"""
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.status = 'draft'
        messages.success(self.request, 'Course created successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('course-detail', kwargs={'pk': self.object.pk})


class CourseDetailView(LoginRequiredMixin, DetailView):
    """Display course details with resources"""
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    
    def get_queryset(self):
        # Show all published courses
        return Course.objects.filter(status='published')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all resources sorted by quality rating
        context['resources'] = self.object.resources.all().order_by('-quality_rating', '-is_official')
        # Check if user is enrolled
        enrollment = CourseEnrollment.objects.filter(
            user=self.request.user,
            course=self.object
        ).first()
        context['enrollment'] = enrollment
        # Check if user is the course creator (for edit/delete buttons)
        context['is_owner'] = self.object.user == self.request.user
        # Group resources by type
        resource_types = {}
        for resource in context['resources']:
            rtype = resource.get_resource_type_display()
            if rtype not in resource_types:
                resource_types[rtype] = []
            resource_types[rtype].append(resource)
        context['resources_by_type'] = resource_types
        return context


class CourseUpdateView(LoginRequiredMixin, UpdateView):
    """Edit an existing course"""
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    
    def get_queryset(self):
        # Only allow user to edit their own courses
        return Course.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Course updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('course-detail', kwargs={'pk': self.object.pk})


class CourseDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a course"""
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('course-list')
    
    def get_queryset(self):
        # Only allow user to delete their own courses
        return Course.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Course deleted successfully!')
        return super().delete(request, *args, **kwargs)


class CourseResourceCreateView(LoginRequiredMixin, CreateView):
    """Add a resource to a course"""
    model = CourseResource
    form_class = CourseResourceForm
    template_name = 'courses/course_resource_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Get course and check ownership
        self.course = get_object_or_404(Course, pk=kwargs['course_pk'], user=request.user)
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.course = self.course
        form.instance.added_by = self.request.user
        messages.success(self.request, 'Resource added successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        return context
    
    def get_success_url(self):
        return reverse_lazy('course-detail', kwargs={'pk': self.course.pk})


class CourseResourceUpdateView(LoginRequiredMixin, UpdateView):
    """Edit a course resource"""
    model = CourseResource
    form_class = CourseResourceForm
    template_name = 'courses/course_resource_form.html'
    
    def get_queryset(self):
        # Only allow editing resources in user's courses
        return CourseResource.objects.filter(course__user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Resource updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.object.course
        return context
    
    def get_success_url(self):
        return reverse_lazy('course-detail', kwargs={'pk': self.object.course.pk})


class CourseResourceDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a course resource"""
    model = CourseResource
    template_name = 'courses/course_resource_confirm_delete.html'
    
    def get_queryset(self):
        # Only allow deleting resources in user's courses
        return CourseResource.objects.filter(course__user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.object.course
        return context
    
    def delete(self, request, *args, **kwargs):
        self.course = self.get_object().course
        messages.success(request, 'Resource deleted successfully!')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('course-detail', kwargs={'pk': self.course.pk})

