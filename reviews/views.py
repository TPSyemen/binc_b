from rest_framework import generics, permissions
from .models import Review
from .serializers import CreateReviewSerializer, ReviewSerializer

class ReviewListCreateView(generics.ListCreateAPIView):
    """API view for listing and creating reviews for a product."""

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_id'])

    def get_serializer_class(self):
        return CreateReviewSerializer if self.request.method == 'POST' else ReviewSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['product_id'] = self.kwargs['product_id']
        return context

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
