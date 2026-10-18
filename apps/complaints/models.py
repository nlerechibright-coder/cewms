from django.db import models
from django.conf import settings
from apps.locations.models import CampusLocation, ComplaintCategory

class Complaint(models.Model):
    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )
    
    STATUS_CHOICES = (
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('NEEDS_INFORMATION', 'Needs Information'),
        ('ACCEPTED', 'Accepted'),
        ('ASSIGNED', 'Assigned'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED_PENDING_VERIFICATION', 'Resolved (Pending Verification)'),
        ('CLOSED', 'Closed'),
        ('REJECTED', 'Rejected'),
    )

    # Core identifiers
    reference_number = models.CharField(max_length=20, unique=True, editable=False, help_text="Public facing ID")
    tracking_token_hash = models.CharField(max_length=128, unique=True, null=True, blank=True, help_text="Hashed credential for anonymous tracking")
    
    # Reporter information (Chapter 3 fields)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints', help_text="Linked user if authenticated")
    full_name = models.CharField(max_length=150, blank=True, help_text="Complainant's full name (for anonymous submissions)")
    contact_address = models.CharField(max_length=200, blank=True, help_text="Contact address (for anonymous submissions)")
    phone = models.CharField(max_length=15, blank=True, help_text="Contact phone (for anonymous submissions)")
    
    # Complaint details (Chapter 3 fields)
    complaint_title = models.CharField(max_length=200, blank=True, help_text="Brief title of the complaint")
    category = models.ForeignKey(ComplaintCategory, on_delete=models.PROTECT, related_name='complaints')
    location = models.ForeignKey(CampusLocation, on_delete=models.PROTECT, related_name='complaints')
    location_desc = models.TextField(blank=True, help_text="Free-text location description (if not in dropdown)")
    complaint_details = models.TextField(help_text="Detailed description of the problem")
    
    # Attachments (handled by ComplaintAttachment model)
    
    # Status and priority
    reporter_declared_urgency = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='NORMAL')
    operational_priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='NORMAL')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='SUBMITTED')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Complaint {self.reference_number} - {self.category.name}"


class ComplaintAttachment(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='complaint_attachments/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.complaint.reference_number}"


class WorkAssignment(models.Model):
    """Chapter 3: ASSIGNMENTS entity"""
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected'),
    )
    
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='assignments')
    officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='assignments', limit_choices_to={'user_type': 'MAINTENANCE_WORKER'})
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='made_assignments', limit_choices_to={'user_type__in': ['ESTATES_ADMIN', 'SYSTEM_ADMIN']})
    assigned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True, help_text="Assignment notes or instructions")

    class Meta:
        ordering = ['-assigned_at']

    def __str__(self):
        return f"Assignment {self.id} - Complaint {self.complaint.reference_number}"


class StatusHistory(models.Model):
    """Chapter 3: STATUS_HISTORY entity"""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='status_history')
    status_value = models.CharField(max_length=30, choices=Complaint.STATUS_CHOICES)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, help_text="Reason for status change")

    class Meta:
        ordering = ['-changed_at']
        verbose_name_plural = "Status Histories"

    def __str__(self):
        return f"{self.complaint.reference_number} -> {self.status_value} at {self.changed_at}"