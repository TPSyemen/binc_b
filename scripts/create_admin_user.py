import os
import sys
import django

def setup_django_environment():
    """Set up the Django environment."""
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'binc_b.settings')
    django.setup()

def create_admin_user():
    """Create an admin user if it doesn't already exist."""
    from core.models import User

    username = "admin"
    email = "admin@example.com"
    password = "admin123"

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            user_type="admin"
        )
        print(f"Admin user '{username}' created successfully.")
    else:
        print(f"Admin user '{username}' already exists.")

if __name__ == "__main__":
    setup_django_environment()
    create_admin_user()
