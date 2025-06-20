"""
reviews/views.py
----------------
Defines review-related API views.
"""

from rest_framework import generics, permissions
from .models import Review
from .serializers import CreateReviewSerializer, ReviewSerializer

class ReviewListCreateView(generics.ListCreateAPIView):
    """API view for listing and creating reviews for a product أو عبر /reviews/add/"""

    def get_queryset(self):
        product_id = self.kwargs.get('product_id') or self.request.data.get('product_id')
        if product_id:
            return Review.objects.filter(product_id=product_id)
        return Review.objects.none()

    def get_serializer_class(self):
        return CreateReviewSerializer if self.request.method == 'POST' else ReviewSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # عند POST عبر /reviews/add/ يجب أخذ product_id من body
        if self.request.method == 'POST':
            product_id = self.request.data.get('product_id')
        else:
            product_id = self.kwargs.get('product_id')
        context['product_id'] = product_id
        return context

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
