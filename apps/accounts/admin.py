from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserProfile

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # What shows in the main table view
    list_display = ('username', 'full_name', 'email', 'phone', 'user_type', 'is_active', 'date_joined')
    
    # Filters on the right side
    list_filter = ('user_type', 'is_active', 'is_staff')
    
    # What fields can be searched using the search bar
    search_fields = ('username', 'full_name', 'email', 'phone')
    
    # How the edit page is organized
    fieldsets = UserAdmin.fieldsets + (
        ('Chapter 3 & Additional Info', {'fields': ('full_name', 'phone', 'user_type')}),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'university_id', 'department', 'is_verified')
    list_filter = ('is_verified', 'department')
    search_fields = ('user__username', 'user__full_name', 'university_id')