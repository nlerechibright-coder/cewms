import secrets
import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Complaint, ComplaintAttachment, WorkAssignment, StatusHistory
from .forms import PublicComplaintForm, ComplaintTrackingForm
from apps.accounts.decorators import maintenance_worker_required

def generate_reference_number():
    """Generate a unique, readable reference number like CMP-20261015-XXXX."""
    date_str = timezone.now().strftime('%Y%m%d')
    random_str = secrets.token_hex(2).upper()  # 4 random hex chars
    return f"CMP-{date_str}-{random_str}"

def generate_tracking_token_hash(raw_token):
    """Hash the tracking token for secure storage."""
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

def public_submit_view(request):
    """Handles the public complaint submission (and logged-in user submission)."""
    if request.method == 'POST':
        form = PublicComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            
            # NEW: If the user is logged in, link the complaint to their account
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
    """Displays the confirmation page with the reference number and tracking token."""
    ref = request.session.get('last_complaint_ref')
    token = request.session.get('last_tracking_token')
    
    if not ref or not token:
        return redirect('complaints:public_submit')
        
    return render(request, 'complaints/submission_success.html', {
        'reference_number': ref,
        'tracking_token': token
    })


def track_complaint_view(request):
    """Allows anonymous users to track their complaint using reference number and token."""
    if request.method == 'POST':
        form = ComplaintTrackingForm(request.POST)
        if form.is_valid():
            ref = form.cleaned_data['reference_number']
            token = form.cleaned_data['tracking_token']
            token_hash = generate_tracking_token_hash(token)
            
            try:
                complaint = Complaint.objects.get(
                    reference_number=ref,
                    tracking_token_hash=token_hash
                )
                return render(request, 'complaints/tracking_result.html', {
                    'complaint': complaint,
                    'show_full_details': False  # Anonymous users see limited info
                })
            except Complaint.DoesNotExist:
                messages.error(request, "Invalid reference number or tracking token. Please check and try again.")
    else:
        form = ComplaintTrackingForm()
    
    return render(request, 'complaints/track_complaint.html', {'form': form})


@login_required
def user_dashboard_view(request):
    """Dashboard for registered users to see their own complaints."""
    user_complaints = Complaint.objects.filter(reporter=request.user).order_by('-created_at')
    return render(request, 'complaints/user_dashboard.html', {
        'complaints': user_complaints,
        'show_full_details': True
    })


@login_required
def complaint_detail_view(request, reference_number):
    """Detailed view of a specific complaint (only accessible by the owner)."""
    complaint = get_object_or_404(Complaint, reference_number=reference_number)
    
    # Security check: only the reporter can view their own complaint
    if complaint.reporter != request.user:
        messages.error(request, "You do not have permission to view this complaint.")
        return redirect('complaints:user_dashboard')
    
    return render(request, 'complaints/complaint_detail.html', {
        'complaint': complaint
    })


@maintenance_worker_required
def officer_dashboard_view(request):
    """Dashboard for maintenance workers to see their assigned jobs."""
    assignments = WorkAssignment.objects.filter(
        officer=request.user
    ).select_related('complaint', 'complaint__category', 'complaint__location').order_by('-assigned_at')
    
    return render(request, 'complaints/officer_dashboard.html', {'assignments': assignments})


@maintenance_worker_required
def officer_job_detail_view(request, assignment_id):
    """Detail view for a specific job assignment, allowing status updates."""
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