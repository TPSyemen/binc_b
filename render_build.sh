#!/usr/bin/env bash
# Exit on error
set -o errexit

# Initial setup
echo "Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Create default site directly in the database
echo "Creating default site..."
python << END
import django
django.setup()
from django.contrib.sites.models import Site
from django.db import connection

# Try to get the site with ID 1
try:
    site = Site.objects.get(id=1)
    site.domain = 'binc-b-1.onrender.com'
    site.name = 'Best In Click'
    site.save()
    print(f"Updated existing site: {site.domain}")
except Site.DoesNotExist:
    # Create a new site if it doesn't exist
    site = Site.objects.create(id=1, domain='binc-b-1.onrender.com', name='Best In Click')
    print(f"Created new site: {site.domain}")
except Exception as e:
    print(f"Error creating site via ORM: {e}")
    print("Trying direct SQL approach...")
    try:
        with connection.cursor() as cursor:
            # Check if the table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='django_site';")
            if cursor.fetchone():
                # Insert or replace the site
                cursor.execute("INSERT OR REPLACE INTO django_site (id, domain, name) VALUES (1, 'binc-b-1.onrender.com', 'Best In Click');")
                print("Created site via direct SQL")
    except Exception as sql_error:
        print(f"Error with direct SQL: {sql_error}")
END

# Also try using the sqlite3 command directly
echo "Trying direct sqlite3 command..."
if [ -f "db.sqlite3" ]; then
    sqlite3 db.sqlite3 < scripts/create_site.sql
    echo "Executed SQL script directly"
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Build completed successfully!"
