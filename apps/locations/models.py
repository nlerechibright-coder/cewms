from django.db import models

class CampusLocation(models.Model):
    name = models.CharField(max_length=150, help_text="e.g., 'Main Library', 'Hostel Block A'")
    code = models.CharField(max_length=20, unique=True, help_text="Short unique code, e.g., 'LIB-01'")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_locations', help_text="Parent location for hierarchy")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Campus Locations"
        ordering = ['name']

    def __str__(self):
        if self.parent:
            return f"{self.name} ({self.parent.name})"
        return self.name


class ComplaintCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g., 'Plumbing', 'Electrical'")
    description = models.TextField(blank=True, help_text="Brief description of what this category covers")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Complaint Categories"
        ordering = ['name']

    def __str__(self):
        return self.name