import secrets
import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from .models import Complaint, ComplaintAttachment, WorkAssignment, StatusHistory
from .forms import PublicComplaintForm, ComplaintTrackingForm
from apps.accounts.models import CustomUser
from apps.accounts.decorators import estates_admin_required, maintenance_worker_required

def generate_reference_number():
    date_str = timezone.now().strftime('%Y%m%d')
    random_str = secrets.token_hex(2).upper()
    return f"CMP-{date_str}-{random_str}"

def generate_tracking_token_hash(raw_token):
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

def public_submit_view(request):
    if request.method == 'POST':
        form = PublicComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            if request.user.is_authenticated:
                complaint.reporter = request.user
            
            complaint.reference_number = generate_reference_number()
            complaint.status = 'SUBMITTED'
            complaint.operational_priority = complaint.reporter_declared_urgency
            
            raw_tracking_token = secrets.token_urlsafe(32)
            complaint.tracking_token_hash = generate_tracking_token_hash(raw_tracking_token)
            complaint.save()
            
            photo = form.cleaned_data.get('photo')
            if photo:
                ComplaintAttachment.objects.create(complaint=complaint, file=photo)
            
            request.session['last_complaint_ref'] = complaint.reference_number
            request.session['last_tracking_token'] = raw_tracking_token
            
            return redirect('complaints:submission_success')
    else:
        form = PublicComplaintForm()

    return render(request, 'complaints/public_submit.html', {'form': form})


def submission_success_view(request):
    ref = request.session.get('last_complaint_ref')
    token = request.session.get('last_tracking_token')
    if not ref or not token:
        return redirect('complaints:public_submit')
    return render(request, 'complaints/submission_success.html', {
        'reference_number': ref,
        'tracking_token': token
    })


def track_complaint_view(request):
    if request.method == 'POST':
        form = ComplaintTrackingForm(request.POST)
        if form.is_valid():
            ref = form.cleaned_data['reference_number']
            token = form.cleaned_data['tracking_token']
            token_hash = generate_tracking_token_hash(token)
            try:
                complaint = Complaint.objects.get(reference_number=ref, tracking_token_hash=token_hash)
                return render(request, 'complaints/tracking_result.html', {
                    'complaint': complaint,
                    'show_full_details': False
                })
            except Complaint.DoesNotExist:
                messages.error(request, "Invalid reference number or tracking token. Please check and try again.")
    else:
        form = ComplaintTrackingForm()
    return render(request, 'complaints/track_complaint.html', {'form': form})


@login_required
def user_dashboard_view(request):
    user_complaints = Complaint.objects.filter(reporter=request.user).order_by('-created_at')
    return render(request, 'complaints/user_dashboard.html', {
        'complaints': user_complaints,
        'show_full_details': True
    })


@login_required
def complaint_detail_view(request, reference_number):
    complaint = get_object_or_404(Complaint, reference_number=reference_number)
    if complaint.reporter != request.user:
        messages.error(request, "You do not have permission to view this complaint.")
        return redirect('complaints:user_dashboard')
    return render(request, 'complaints/complaint_detail.html', {'complaint': complaint})


@estates_admin_required
def management_complaints_view(request):
    complaints = Complaint.objects.all().select_related('category', 'location', 'reporter').order_by('-created_at')
    return render(request, 'complaints/management_complaints.html', {'complaints': complaints})


@estates_admin_required
def assign_complaint_view(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    engineers = CustomUser.objects.filter(user_type='MAINTENANCE_WORKER', is_active=True).order_by('discipline', 'username')
    
    if request.method == 'POST':
        engineer_id = request.POST.get('engineer')
        notes = request.POST.get('notes', '')
        
        if engineer_id:
            engineer = get_object_or_404(CustomUser, id=engineer_id, user_type='MAINTENANCE_WORKER')
            
            WorkAssignment.objects.create(
                complaint=complaint,
                officer=engineer,
                assigned_by=request.user,
                status='PENDING',
                notes=notes
            )
            
            old_status = complaint.status
            complaint.status = 'ASSIGNED'
            complaint.save()
            
            StatusHistory.objects.create(
                complaint=complaint,
                status_value='ASSIGNED',
                changed_by=request.user,
                remarks=f"Assigned to {engineer.full_name or engineer.username} ({engineer.get_discipline_display()}). Notes: {notes}"
            )
            
            messages.success(request, f"Complaint successfully assigned to {engineer.username}.")
            return redirect('complaints:management_complaints')
        else:
            messages.error(request, "Please select an engineer to assign.")
            
    return render(request, 'complaints/assign_complaint.html', {
        'complaint': complaint,
        'engineers': engineers
    })


@maintenance_worker_required
def officer_dashboard_view(request):
    assignments = WorkAssignment.objects.filter(
        officer=request.user
    ).select_related('complaint', 'complaint__category', 'complaint__location').order_by('-assigned_at')
    return render(request, 'complaints/officer_dashboard.html', {'assignments': assignments})


@maintenance_worker_required
def officer_job_detail_view(request, assignment_id):
    assignment = get_object_or_404(WorkAssignment, id=assignment_id, officer=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status and new_status != assignment.status:
            old_status = assignment.status
            assignment.status = new_status
            assignment.notes = notes
            assignment.save()
            
            complaint = assignment.complaint
            if new_status == 'ACCEPTED':
                complaint.status = 'ACKNOWLEDGED'
            elif new_status == 'IN_PROGRESS':
                complaint.status = 'IN_PROGRESS'
            elif new_status == 'COMPLETED':
                complaint.status = 'RESOLVED_PENDING_VERIFICATION'
            complaint.save()
            
            StatusHistory.objects.create(
                complaint=complaint,
                status_value=complaint.status,
                changed_by=request.user,
                remarks=f"Officer updated assignment from {old_status} to {new_status}. Notes: {notes}"
            )
            messages.success(request, "Job status updated successfully.")
            return redirect('complaints:officer_job_detail', assignment_id=assignment.id)
        else:
            assignment.notes = notes
            assignment.save()
            messages.info(request, "Notes updated.")
            return redirect('complaints:officer_job_detail', assignment_id=assignment.id)

    return render(request, 'complaints/officer_job_detail.html', {'assignment': assignment})