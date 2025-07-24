#!/usr/bin/env python
"""
Development setup script to initialize the Django project.
This script handles database setup and initial configuration.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_development():
    """Setup development environment."""
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'binc_b.settings')
    
    # Initialize Django
    django.setup()
    
    print("🚀 Setting up development environment...")
    
    try:
        # Create migrations
        print("📝 Creating migrations...")
        execute_from_command_line(['manage.py', 'makemigrations'])
        
        # Apply migrations
        print("🔄 Applying migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        # Setup site configuration
        print("🌐 Setting up site configuration...")
        execute_from_command_line(['manage.py', 'setup_site'])
        
        # Create superuser (optional)
        print("👤 You can create a superuser by running:")
        print("   python manage.py createsuperuser")
        
        print("✅ Development environment setup complete!")
        print("🎯 You can now run: python manage.py runserver")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        return False
    
    return True

if __name__ == '__main__':
    setup_development()
