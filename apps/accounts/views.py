from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView
from django.contrib.auth import views as auth_views
from django.contrib import messages
from .models import CustomUser
from .forms import CustomUserCreationForm, EngineerCreationForm
from apps.complaints.models import Complaint, WorkAssignment
from apps.accounts.decorators import estates_admin_required, system_admin_required

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('accounts:dashboard')
    template_name = 'accounts/register.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class CustomLoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    
    def get_success_url(self):
        user = self.request.user
        if user.user_type == 'SYSTEM_ADMIN':
            return reverse('accounts:administrator_dashboard')
        elif user.user_type == 'ESTATES_ADMIN':
            return reverse('accounts:management_dashboard')
        elif user.is_maintenance_worker:
            return reverse('complaints:officer_dashboard')
        else:
            return reverse('accounts:dashboard')

@login_required
def dashboard_view(request):
    user = request.user
    context = {'user': user}
    my_complaints = Complaint.objects.filter(reporter=user)
    context['my_complaints'] = my_complaints
    context['total_submitted'] = my_complaints.count()
    context['active_complaints'] = my_complaints.exclude(status__in=['CLOSED', 'REJECTED']).count()
    return render(request, 'accounts/dashboard.html', context)


@estates_admin_required
def management_dashboard_view(request):
    """The custom dashboard for Estates Admins (Management)."""
    
    # 1. Get the counts for the summary cards
    total_complaints = Complaint.objects.count()
    pending_complaints = Complaint.objects.filter(status='SUBMITTED').count()
    assigned_complaints = Complaint.objects.filter(status='ASSIGNED').count()
    in_progress_complaints = Complaint.objects.filter(status='IN_PROGRESS').count()
    resolved_complaints = Complaint.objects.filter(status='RESOLVED_PENDING_VERIFICATION').count()
    
    # 2. FIX: Query the actual complaints to display in a list
    recent_complaints = Complaint.objects.select_related('category', 'location').order_by('-created_at')[:10]

    context = {
        'user': request.user,
        'total_complaints': total_complaints,
        'pending_complaints': pending_complaints,
        'assigned_complaints': assigned_complaints,
        'in_progress_complaints': in_progress_complaints,
        'resolved_complaints': resolved_complaints,
        'recent_complaints': recent_complaints, # Pass the list to the template
    }
    return render(request, 'accounts/management_dashboard.html', context)


@system_admin_required
def administrator_dashboard_view(request):
    """Dedicated application dashboard for CEWMS system administrators."""
    complaints = Complaint.objects.select_related('category', 'location', 'reporter').order_by('-created_at')
    context = {
        'total_complaints': complaints.count(),
        'submitted_complaints': complaints.filter(status='SUBMITTED').count(),
        'assigned_complaints': complaints.filter(status='ASSIGNED').count(),
        'engineer_count': CustomUser.objects.filter(user_type='MAINTENANCE_WORKER').count(),
        'user_count': CustomUser.objects.count(),
        'recent_complaints': complaints[:20],
        'engineers': CustomUser.objects.filter(user_type='MAINTENANCE_WORKER').order_by('username'),
        'users': CustomUser.objects.exclude(user_type='MAINTENANCE_WORKER').order_by('user_type', 'username')[:20],
    }
    return render(request, 'accounts/administrator_dashboard.html', context)


@estates_admin_required
def engineer_list_view(request):
    engineers = CustomUser.objects.filter(user_type='MAINTENANCE_WORKER').order_by('discipline', 'username')
    
    if request.method == 'POST':
        engineer_id = request.POST.get('engineer_id')
        action = request.POST.get('action')
        
        if engineer_id and action in ['activate', 'deactivate']:
            engineer = get_object_or_404(CustomUser, id=engineer_id, user_type='MAINTENANCE_WORKER')
            engineer.is_active = (action == 'activate')
            engineer.save()
            status = "activated" if action == 'activate' else "deactivated"
            messages.success(request, f"Engineer {engineer.username} has been {status}.")
            
        return redirect('accounts:engineer_list')
        
    return render(request, 'accounts/engineer_list.html', {'engineers': engineers})


@estates_admin_required
def create_engineer_view(request):
    if request.method == 'POST':
        form = EngineerCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "New engineer account created successfully!")
            return redirect('accounts:engineer_list')
    else:
        form = EngineerCreationForm()
    return render(request, 'accounts/create_engineer.html', {'form': form})


def custom_logout_view(request):
    logout(request)
    return redirect('accounts:login')
