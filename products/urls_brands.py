from rest_framework.routers import DefaultRouter
from .views import BrandViewSet

router = DefaultRouter()
router.register(r'', BrandViewSet, basename='brand')

urlpatterns = router.urls
