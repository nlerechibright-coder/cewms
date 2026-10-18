from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages

class EstatesAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin for class-based views that require Estates Admin or System Admin privileges.
    """
    def test_func(self):
        return self.request.user.is_estates_admin
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        
        messages.error(self.request, "You do not have permission to access this page.")
        return redirect('accounts:dashboard')


class MaintenanceWorkerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin for class-based views that require Maintenance Worker privileges.
    """
    def test_func(self):
        return self.request.user.is_maintenance_worker
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        
        messages.error(self.request, "You do not have permission to access this page.")
        return redirect('accounts:dashboard')


class StaffOrAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin for class-based views that require Staff, Estates Admin, or System Admin privileges.
    """
    def test_func(self):
        return self.request.user.user_type in ['STAFF', 'ESTATES_ADMIN', 'SYSTEM_ADMIN']
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        
        messages.error(self.request, "You do not have permission to access this page.")
        return redirect('accounts:dashboard')