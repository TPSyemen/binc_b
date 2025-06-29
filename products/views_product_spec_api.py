from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from core.models import Product, Specification, ProductSpecification
from .serializers import ProductSpecificationSerializer
from core.permissions import IsOwnerUser

class ProductSpecificationListCreate(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsOwnerUser()]

    def get(self, request, product_id):
        """List all specifications for a product (with values)."""
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        specs = ProductSpecification.objects.filter(product=product)
        serializer = ProductSpecificationSerializer(specs, many=True)
        return Response(serializer.data)

    def post(self, request, product_id):
        """Add one or more specifications to a product (only owner)."""
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        specs_data = request.data.get('specifications', [])
        created = []
        for spec in specs_data:
            spec['product'] = str(product.id)
            serializer = ProductSpecificationSerializer(data=spec)
            if serializer.is_valid():
                serializer.save(product=product)
                created.append(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(created, status=status.HTTP_201_CREATED)

class ProductSpecificationDetail(APIView):

    def get_permissions(self):
        return [permissions.IsAuthenticated(), IsOwnerUser()]

    def put(self, request, product_id, spec_id):
        """Update a specification value for a product (only owner)."""
        try:
            ps = ProductSpecification.objects.get(product_id=product_id, id=spec_id)
        except ProductSpecification.DoesNotExist:
            return Response({"error": "Specification not found for this product."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSpecificationSerializer(ps, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, product_id, spec_id):
        """Delete a specification from a product (only owner)."""
        try:
            ps = ProductSpecification.objects.get(product_id=product_id, id=spec_id)
        except ProductSpecification.DoesNotExist:
            return Response({"error": "Specification not found for this product."}, status=status.HTTP_404_NOT_FOUND)
        ps.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
