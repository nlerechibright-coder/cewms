from django import forms
from .models import Complaint, ComplaintAttachment
from apps.locations.models import CampusLocation, ComplaintCategory

class PublicComplaintForm(forms.ModelForm):
    complaint_title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Leaking pipe in restroom'})
    )
    location = forms.ModelChoiceField(
        queryset=CampusLocation.objects.filter(is_active=True),
        empty_label="Select a location...",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_location'})
    )
    location_desc = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Behind the main building, near the parking lot', 'id': 'id_location_desc'}),
        help_text="Required if you selected 'Other / Not Listed' above."
    )
    category = forms.ModelChoiceField(
        queryset=ComplaintCategory.objects.filter(is_active=True),
        empty_label="Select a category...",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    complaint_details = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the problem in detail...'}),
        help_text="Please provide as much detail as possible."
    )
    full_name = forms.CharField(
        max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your full name (optional)'})
    )
    contact_address = forms.CharField(
        max_length=200, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your address (optional)'})
    )
    phone = forms.CharField(
        max_length=15, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your phone number (optional)'})
    )
    reporter_declared_urgency = forms.ChoiceField(
        choices=Complaint.PRIORITY_CHOICES,
        initial='NORMAL',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        help_text="Optional: Upload a photo of the issue (Max 5MB)."
    )

    class Meta:
        model = Complaint
        fields = [
            'complaint_title', 'location', 'location_desc', 'category', 
            'complaint_details', 'full_name', 'contact_address', 'phone', 
            'reporter_declared_urgency'
        ]

    def clean_photo(self):
        """Validate file size and type."""
        photo = self.cleaned_data.get('photo')
        if photo:
            if photo.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("Photo file size must be under 5MB.")
            if not photo.content_type.startswith('image/'):
                raise forms.ValidationError("Only image files are allowed.")
        return photo

    def clean(self):
        """Ensure location_desc is provided if 'Other' is selected."""
        cleaned_data = super().clean()
        location = cleaned_data.get('location')
        location_desc = cleaned_data.get('location_desc')
        
        if location and 'Other' in location.name:
            if not location_desc or not location_desc.strip():
                self.add_error('location_desc', 'Please specify the location since you selected "Other / Not Listed".')
        return cleaned_data


class ComplaintTrackingForm(forms.Form):
    """Form for anonymous users to track their complaint."""
    reference_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., CMP-20261015-A1B2'})
    )
    tracking_token = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your secure tracking token'})
    )