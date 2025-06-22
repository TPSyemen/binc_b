from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sites.models import Site
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.parsers import JSONParser
from core.models import Shop
from products.serializers import ShopSerializer

@csrf_exempt
def ensure_site_view(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed.'}, status=405)
    domain = os.environ.get('SITE_DOMAIN', request.get_host() or 'localhost')
    name = os.environ.get('SITE_NAME', 'localhost')
    # معالجة تكرار الدومين
    site = None
    try:
        site = Site.objects.get(domain=domain)
        site.name = name
        site.save()
    except Site.DoesNotExist:
        # إذا لم يوجد دومين مطابق، عدل أول كائن أو أنشئ جديد
        site, created = Site.objects.get_or_create(id=1, defaults={"domain": domain, "name": name})
        if not created:
            site.domain = domain
            site.name = name
            site.save()
    return JsonResponse({'success': True, 'domain': site.domain, 'name': site.name})

class AdminShopListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser]
    def get(self, request):
        if getattr(request.user, 'user_type', None) != 'admin':
            return Response({'error': 'Not allowed'}, status=403)
        shops = Shop.objects.all()
        return Response(ShopSerializer(shops, many=True).data)
