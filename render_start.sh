#!/usr/bin/env bash
# Exit on error
set -o errexit

# Verify site exists before starting
echo "Verifying site configuration..."
python << END
import django
django.setup()
from django.contrib.sites.models import Site
from django.db import connection

# Try multiple approaches to ensure the site exists
try:
    # Try ORM first
    site, created = Site.objects.get_or_create(
        id=1,
        defaults={
            'domain': 'binc-b-1.onrender.com',
            'name': 'Best In Click'
        }
    )
    if created:
        print(f"Created new site: {site.domain}")
    else:
        print(f"Site exists: {site.domain}")
        # Update it just to be sure
        site.domain = 'binc-b-1.onrender.com'
        site.name = 'Best In Click'
        site.save()
except Exception as e:
    print(f"Error with ORM: {e}")
    print("Trying direct SQL approach...")
    try:
        with connection.cursor() as cursor:
            # Check if the table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='django_site';")
            if cursor.fetchone():
                # Insert or replace the site
                cursor.execute("INSERT OR REPLACE INTO django_site (id, domain, name) VALUES (1, 'binc-b-1.onrender.com', 'Best In Click');")
                print("Created/updated site via direct SQL")
    except Exception as sql_error:
        print(f"Error with direct SQL: {sql_error}")
END

# Also try using the sqlite3 command directly
echo "Trying direct sqlite3 command..."
if [ -f "db.sqlite3" ]; then
    sqlite3 db.sqlite3 < scripts/create_site.sql
    echo "Executed SQL script directly"
fi

# Start Gunicorn
echo "Starting Gunicorn..."
gunicorn binc_b.wsgi:application
