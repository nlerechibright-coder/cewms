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
from apps.accounts.decorators import estates_admin_required

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
        if user.is_estates_admin:
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
    context = {
        'user': request.user,
        'total_complaints': Complaint.objects.count(),
        'pending_complaints': Complaint.objects.filter(status='SUBMITTED').count(),
        'assigned_complaints': Complaint.objects.filter(status='ASSIGNED').count(),
        'in_progress_complaints': Complaint.objects.filter(status='IN_PROGRESS').count(),
        'resolved_complaints': Complaint.objects.filter(status='RESOLVED_PENDING_VERIFICATION').count(),
    }
    return render(request, 'accounts/management_dashboard.html', context)


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