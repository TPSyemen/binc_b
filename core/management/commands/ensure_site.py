from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
import os

class Command(BaseCommand):
    help = 'Ensure a default Site object exists (for admin login and sites framework)'

    def handle(self, *args, **options):
        domain = os.environ.get('SITE_DOMAIN', 'localhost')
        name = os.environ.get('SITE_NAME', 'localhost')
        site, created = Site.objects.get_or_create(id=1, defaults={"domain": domain, "name": name})
        if not created:
            site.domain = domain
            site.name = name
            site.save()
        self.stdout.write(self.style.SUCCESS(f"Site ensured: {site.domain} ({site.name})"))
