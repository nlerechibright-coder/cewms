from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    path('submit/', views.public_submit_view, name='public_submit'),
    path('submit/success/', views.submission_success_view, name='submission_success'),
    path('track/', views.track_complaint_view, name='track_complaint'),
    path('my-complaints/', views.user_dashboard_view, name='user_dashboard'),
    path('my-complaints/<str:reference_number>/', views.complaint_detail_view, name='complaint_detail'),
    
    # Officer Workflow URLs
    path('officer/dashboard/', views.officer_dashboard_view, name='officer_dashboard'),
    path('officer/jobs/<int:assignment_id>/', views.officer_job_detail_view, name='officer_job_detail'),
]