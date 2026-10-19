from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def estates_admin_required(view_func):
    """
    Decorator for views that require Estates Admin or System Admin privileges.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if not request.user.is_estates_admin:
            messages.error(request, "You do not have permission to access this page.")
            return redirect('accounts:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def system_admin_required(view_func):
    """Require the dedicated CEWMS administrator role."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.user_type != 'SYSTEM_ADMIN':
            messages.error(request, "You do not have permission to access this page.")
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def maintenance_worker_required(view_func):
    """
    Decorator for views that require Maintenance Worker privileges.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if not request.user.is_maintenance_worker:
            messages.error(request, "You do not have permission to access this page.")
            return redirect('accounts:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def staff_or_admin_required(view_func):
    """
    Decorator for views that require Staff, Estates Admin, or System Admin privileges.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if request.user.user_type not in ['STAFF', 'ESTATES_ADMIN', 'SYSTEM_ADMIN']:
            messages.error(request, "You do not have permission to access this page.")
            return redirect('accounts:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view
