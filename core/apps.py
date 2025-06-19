from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """
        Run when the app is ready.
        This is a good place to create the default site if it doesn't exist.
        """
        # Import here to avoid circular imports
        from django.contrib.sites.models import Site
        from django.db import DatabaseError

        try:
            # Try to get or create the default site
            site, created = Site.objects.get_or_create(
                id=1,
                defaults={
                    'domain': 'binc-b-1.onrender.com',
                    'name': 'Best In Click'
                }
            )

            # If the site exists but has different values, update it
            if not created and (site.domain != 'binc-b-1.onrender.com' or site.name != 'Best In Click'):
                site.domain = 'binc-b-1.onrender.com'
                site.name = 'Best In Click'
                site.save()
        except DatabaseError:
            # This can happen during migrations when the sites table doesn't exist yet
            pass
