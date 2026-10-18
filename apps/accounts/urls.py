from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Registration
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # Login (using Django's secure built-in view)
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    
    # Logout
    path('logout/', views.custom_logout_view, name='logout'),
    
    # Protected Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
]