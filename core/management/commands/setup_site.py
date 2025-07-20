"""
Management command to setup the default Site object.
This avoids database access during app initialization.
"""

from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Setup the default Site object for the application'

    def handle(self, *args, **options):
        """Setup the default site configuration."""
        try:
            # Try to get or create the default site
            site, created = Site.objects.get_or_create(
                id=1,
                defaults={
                    'domain': 'localhost:8000',
                    'name': 'Best In Click'
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created new site: {site.domain}')
                )
            else:
                # Update the site if needed
                updated = False
                if site.domain != 'localhost:8000':
                    site.domain = 'localhost:8000'
                    updated = True
                if site.name != 'Best In Click':
                    site.name = 'Best In Click'
                    updated = True
                
                if updated:
                    site.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Updated site: {site.domain}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'Site already configured: {site.domain}')
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting up site: {e}')
            )
