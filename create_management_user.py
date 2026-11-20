import os
import sys
import django

# 1. Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# 2. Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# 3. Import model
try:
    from accounts.models import CustomUser
except ImportError:
    from apps.accounts.models import CustomUser

def run():
    username = 'Lincoln1234'
    
    try:
        user = CustomUser.objects.get(username=username)
        user.role = 'management'
        user.save()
        print(f"✅ Successfully updated {username} to 'management' role!")
    except CustomUser.DoesNotExist:
        print(f"❌ User '{username}' not found.")
    except Exception as e:
        print(f" Error: {e}")

if __name__ == '__main__':
    run()