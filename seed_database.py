import os
import sys
import django

# 1. Setup paths and Django environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# IMPORTANT: If your settings are in 'cewms.settings', change 'config.settings' to 'cewms.settings'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

# Dynamically import models to prevent crashes if names differ slightly
try:
    from locations.models import Location, Category
except ImportError:
    Location = None
    Category = None

User = get_user_model()

def seed_management_user():
    print("🌱 [1/3] Seeding Management User...")
    username = 'Lincoln1234'
    password = 'school12345'
    
    # Create or get the user
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
        print(f"ℹ️  User '{username}' already exists. Updating permissions...")
    else:
        # Create as superuser to guarantee full access
        user = User.objects.create_superuser(
            username=username,
            email='management@cewms.com',
            password=password
        )
        print(f"✅ Created superuser: {username}")

    # Try to update the role if the model actually has a 'role' field
    if hasattr(user, 'role'):
        # Note: Change 'management' to 'admin' or 'owner' if those are your actual role choices
        user.role = 'management' 
        user.save()
        print(f"✅ Updated role to 'management'.")

    # Ensure they are in a Management group (common in compliance systems)
    mgmt_group, _ = Group.objects.get_or_create(name='Management')
    if mgmt_group not in user.groups.all():
        user.groups.add(mgmt_group)
        print(f"✅ Added {username} to 'Management' group.")

def seed_locations_and_categories():
    print("🌱 [2/3] Seeding Locations and Categories...")
    
    if Category:
        categories = ['Facility Issue', 'Safety Hazard', 'IT/Network', 'Academic', 'Administrative', 'Health']
        created_count = 0
        for cat_name in categories:
            # Use get_or_create to avoid duplicates. Adjust 'name' to 'title' if your model uses that.
            try:
                Category.objects.get_or_create(name=cat_name)
                created_count += 1
            except Exception:
                try:
                    Category.objects.get_or_create(title=cat_name)
                except Exception:
                    pass
        print(f"✅ Seeded {created_count} default categories.")
    else:
        print("⚠️ Category model not found, skipping.")

    if Location:
        locations = ['Main Building', 'Library', 'Science Lab', 'Cafeteria', 'Sports Complex', 'Administration Block', 'Parking Lot']
        created_count = 0
        for loc_name in locations:
            try:
                Location.objects.get_or_create(name=loc_name)
                created_count += 1
            except Exception:
                try:
                    Location.objects.get_or_create(title=loc_name)
                except Exception:
                    pass
        print(f"✅ Seeded {created_count} default locations.")
    else:
        print("⚠️ Location model not found, skipping.")

def run():
    print("🚀 ==========================================")
    print("🚀 Starting Database Seeding for CEWMS...")
    print("🚀 ==========================================")
    
    seed_management_user()
    seed_locations_and_categories()
    
    print(" ==========================================")
    print(" Database seeding complete!")
    print(" ==========================================")

if __name__ == '__main__':
    run()