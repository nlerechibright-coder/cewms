from django.db import migrations

def add_common_locations(apps, schema_editor):
    CampusLocation = apps.get_model('locations', 'CampusLocation')
    locations = [
        {'name': 'Main Library', 'code': 'LIB-01'},
        {'name': 'Hostel Block A', 'code': 'HST-A'},
        {'name': 'Lecture Hall Complex', 'code': 'LHC-01'},
        {'name': 'ICT Center', 'code': 'ICT-01'},
        {'name': 'Cafeteria / Dining Hall', 'code': 'CAF-01'},
        {'name': 'Other / Not Listed', 'code': 'OTH-01'},
    ]
    for loc in locations:
        CampusLocation.objects.get_or_create(
            code=loc['code'],
            defaults={'name': loc['name'], 'is_active': True}
        )

def remove_common_locations(apps, schema_editor):
    CampusLocation = apps.get_model('locations', 'CampusLocation')
    codes = ['LIB-01', 'HST-A', 'LHC-01', 'ICT-01', 'CAF-01', 'OTH-01']
    CampusLocation.objects.filter(code__in=codes).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('locations', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_common_locations, remove_common_locations),
    ]