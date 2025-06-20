from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sites.models import Site
import os

@csrf_exempt
def ensure_site_view(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed.'}, status=405)
    domain = os.environ.get('SITE_DOMAIN', request.get_host() or 'localhost')
    name = os.environ.get('SITE_NAME', 'localhost')
    site, created = Site.objects.get_or_create(id=1, defaults={"domain": domain, "name": name})
    if not created:
        site.domain = domain
        site.name = name
        site.save()
    return JsonResponse({'success': True, 'domain': site.domain, 'name': site.name})
