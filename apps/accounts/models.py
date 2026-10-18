from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('STUDENT', 'Student'),
        ('STAFF', 'University Staff'),
        ('MAINTENANCE_WORKER', 'Maintenance Worker'),
        ('ESTATES_ADMIN', 'Estates & Works Admin'),
        ('SYSTEM_ADMIN', 'System Administrator'),
    )
    
    # Chapter 3 required fields
    full_name = models.CharField(max_length=150, blank=True, help_text="User's full name")
    phone = models.CharField(max_length=15, blank=True, help_text="Contact phone number")
    
    # Existing fields
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='STUDENT')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    @property
    def is_estates_admin(self):
        return self.user_type in ['ESTATES_ADMIN', 'SYSTEM_ADMIN']

    @property
    def is_maintenance_worker(self):
        return self.user_type == 'MAINTENANCE_WORKER'


class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    university_id = models.CharField(max_length=50, unique=True, null=True, blank=True, help_text="Matriculation or Staff ID")
    department = models.CharField(max_length=100, null=True, blank=True)
    is_verified = models.BooleanField(default=False, help_text="Administrator approved or system verified")

    def __str__(self):
        return f"Profile for {self.user.username}"