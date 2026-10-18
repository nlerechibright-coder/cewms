from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CustomUserCreationForm
from apps.complaints.models import Complaint, WorkAssignment

class RegisterView(CreateView):
    """
    Handles user registration. 
    If successful, logs the user in and redirects to their dashboard.
    """
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('accounts:dashboard')
    template_name = 'accounts/register.html'

    def form_valid(self, form):
        # Save the user and log them in automatically
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


@login_required
def dashboard_view(request):
    """
    The protected dashboard for authenticated users.
    Shows role-specific information and navigation.
    """
    user = request.user
    context = {'user': user}
    
    # Role-specific dashboard data
    if user.is_estates_admin:
        # Estates Admin: Show complaint management stats
        context['total_complaints'] = Complaint.objects.count()
        context['pending_complaints'] = Complaint.objects.filter(status='SUBMITTED').count()
        context['assigned_complaints'] = Complaint.objects.filter(status='ASSIGNED').count()
        context['in_progress_complaints'] = Complaint.objects.filter(status='IN_PROGRESS').count()
        context['resolved_complaints'] = Complaint.objects.filter(status='RESOLVED_PENDING_VERIFICATION').count()
        
    elif user.is_maintenance_worker:
        # Maintenance Worker: Show their assigned jobs
        my_assignments = WorkAssignment.objects.filter(officer=user).select_related('complaint')
        context['my_assignments'] = my_assignments
        context['pending_jobs'] = my_assignments.filter(status='PENDING').count()
        context['in_progress_jobs'] = my_assignments.filter(status='IN_PROGRESS').count()
        context['completed_jobs'] = my_assignments.filter(status='COMPLETED').count()
        
    else:
        # Student/Staff: Show their submitted complaints
        my_complaints = Complaint.objects.filter(reporter=user)
        context['my_complaints'] = my_complaints
        context['total_submitted'] = my_complaints.count()
        context['active_complaints'] = my_complaints.exclude(status__in=['CLOSED', 'REJECTED']).count()
    
    return render(request, 'accounts/dashboard.html', context)


def custom_logout_view(request):
    """
    Handles user logout securely.
    """
    logout(request)
    return redirect('accounts:login')