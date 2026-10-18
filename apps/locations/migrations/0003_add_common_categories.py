from django.db import migrations

def add_common_categories(apps, schema_editor):
    ComplaintCategory = apps.get_model('locations', 'ComplaintCategory')
    categories = [
        {'name': 'Plumbing', 'description': 'Leaks, broken pipes, drainage issues, blocked toilets'},
        {'name': 'Electrical', 'description': 'Flickering lights, broken sockets, wiring issues, power outages'},
        {'name': 'Carpentry/Furniture', 'description': 'Broken desks, chairs, doors, windows, or locks'},
        {'name': 'Cleaning/Sanitation', 'description': 'Trash accumulation, pest control, general cleanliness'},
        {'name': 'HVAC', 'description': 'Air conditioning, heating, or ventilation issues'},
        {'name': 'Other', 'description': 'Any other maintenance or facility issue not listed above'},
    ]
    for cat in categories:
        ComplaintCategory.objects.get_or_create(
            name=cat['name'],
            defaults={'description': cat['description'], 'is_active': True}
        )

def remove_common_categories(apps, schema_editor):
    ComplaintCategory = apps.get_model('locations', 'ComplaintCategory')
    names = ['Plumbing', 'Electrical', 'Carpentry/Furniture', 'Cleaning/Sanitation', 'HVAC', 'Other']
    ComplaintCategory.objects.filter(name__in=names).delete()

class Migration(migrations.Migration):
    # NOTE: Update the dependency below to match your latest locations migration (e.g., '0002_add_common_locations')
    dependencies = [
        ('locations', '0002_add_common_locations'), 
    ]

    operations = [
        migrations.RunPython(add_common_categories, remove_common_categories),
    ]