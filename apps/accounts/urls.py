from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('management/dashboard/', views.management_dashboard_view, name='management_dashboard'),
    path('engineers/', views.engineer_list_view, name='engineer_list'),
    path('create-engineer/', views.create_engineer_view, name='create_engineer'),
]