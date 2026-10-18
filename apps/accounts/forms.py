from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """
    A form that creates a user, with no privileges, from the given username and password.
    Includes Chapter 3 required fields: full_name and phone.
    """
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'})
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your phone number (optional)'})
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'full_name', 'phone', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'STUDENT' # Default role for new registrants
        if commit:
            user.save()
        return user


class EngineerCreationForm(UserCreationForm):
    """
    A secure form for Estates Admin to create Maintenance Worker accounts.
    """
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Engineer\'s full name'})
    )
    phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Engineer\'s phonenumber'})
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'full_name', 'phone', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'MAINTENANCE_WORKER' # Hardcoded role for this form
        if commit:
            user.save()
        return user


class AdminCreationForm(UserCreationForm):
    """
    Form for creating the initial 2 Management accounts.
    CRITICAL: Ensures the account is saved as an ESTATES_ADMIN so it persists correctly.
    """
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Admin full name'})
    )
    phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Admin phone number'})
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'full_name', 'phone', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        # CRITICAL FIX: This ensures the account is actually saved as an Admin
        user.user_type = 'ESTATES_ADMIN' 
        user.is_staff = True # Required to access admin features if needed
        if commit:
            user.save()
        return user