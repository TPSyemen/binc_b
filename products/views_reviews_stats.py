from rest_framework import generics, permissions
from rest_framework.response import Response
from reviews.models import Review
from reviews.serializers import ReviewSerializer
from core.models import Product

class ProductReviewsStatsView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk):
        product = Product.objects.get(pk=pk)
        reviews = Review.objects.filter(product=product)
        likes = product.likes
        dislikes = product.dislikes
        neutrals = product.neutrals
        views = product.views
        rating = float(product.rating)
        users_liked = reviews.filter(rating__gte=4).count()
        return Response({
            'reviews': ReviewSerializer(reviews, many=True).data,
            'likes': likes,
            'dislikes': dislikes,
            'neutrals': neutrals,
            'views': views,
            'users_liked': users_liked,
            'rating': rating,
            'reviews_count': reviews.count(),
        })
