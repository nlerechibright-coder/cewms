import os
import sys
import django

# 1. Setup paths and Django environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# 2. Import the model
try:
    from accounts.models import CustomUser
except ImportError:
    from apps.accounts.models import CustomUser

def run():
    username = 'Lincoln1234'
    
    try:
        # Find the user
        user = CustomUser.objects.get(username=username)
        
        # Change the user_type from STUDENT to SYSTEM_ADMIN
        user.user_type = 'SYSTEM_ADMIN'
        user.save()
        
        print(f"✅ Success! {user.username} is now a {user.get_user_type_display()}")
        
    except CustomUser.DoesNotExist:
        print(f"❌ User '{username}' not found.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    run()