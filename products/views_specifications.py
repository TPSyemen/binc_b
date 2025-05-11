from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from core.models import SpecificationCategory, Specification, ProductSpecification, Product
from .serializers import SpecificationCategorySerializer, SpecificationSerializer, ProductSpecificationSerializer

class SpecificationCategoryListView(APIView):
    """
    API view for listing specification categories.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all specification categories with their specifications."""
        # Verificar si el usuario es propietario o administrador
        if request.user.user_type not in ['owner', 'admin']:
            return Response(
                {"error": "You must be an owner or admin to access this feature."},
                status=status.HTTP_403_FORBIDDEN
            )

        categories = SpecificationCategory.objects.all()
        result = []

        for category in categories:
            category_data = {
                'id': str(category.id),
                'category_name': category.category_name,
                'specifications': []
            }

            specifications = Specification.objects.filter(category=category)
            for spec in specifications:
                category_data['specifications'].append({
                    'id': str(spec.id),
                    'specification_name': spec.specification_name
                })

            result.append(category_data)

        return Response(result)

class ProductSpecificationsView(APIView):
    """
    API view for managing product specifications.
    """
    permission_classes = [IsAuthenticated]

    def get_product(self, product_id):
        """Get product object."""
        try:
            return Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return None

    def get(self, request, product_id):
        """Get specifications for a product."""
        # Verificar si el usuario es propietario o administrador
        if request.user.user_type not in ['owner', 'admin']:
            return Response(
                {"error": "You must be an owner or admin to access this feature."},
                status=status.HTTP_403_FORBIDDEN
            )

        product = self.get_product(product_id)
        if not product:
            return Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verificar si el usuario es el propietario del producto
        if request.user.user_type == 'owner' and product.shop.owner.user != request.user:
            return Response(
                {"error": "You can only access specifications for your own products."},
                status=status.HTTP_403_FORBIDDEN
            )

        product_specs = ProductSpecification.objects.filter(product=product)
        result = []

        for spec in product_specs:
            result.append({
                'specification_id': str(spec.specification.id),
                'specification_name': spec.specification.specification_name,
                'category_id': str(spec.specification.category.id),
                'category_name': spec.specification.category.category_name,
                'value': spec.specification_value
            })

        return Response(result)

    def post(self, request, product_id):
        """Save specifications for a product."""
        # Verificar si el usuario es propietario o administrador
        if request.user.user_type not in ['owner', 'admin']:
            return Response(
                {"error": "You must be an owner or admin to access this feature."},
                status=status.HTTP_403_FORBIDDEN
            )

        product = self.get_product(product_id)
        if not product:
            return Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verificar si el usuario es el propietario del producto
        if request.user.user_type == 'owner' and product.shop.owner.user != request.user:
            return Response(
                {"error": "You can only update specifications for your own products."},
                status=status.HTTP_403_FORBIDDEN
            )

        specifications = request.data.get('specifications', [])
        if not specifications:
            return Response(
                {"error": "No specifications provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Eliminar especificaciones existentes
        ProductSpecification.objects.filter(product=product).delete()

        # Crear nuevas especificaciones
        created_specs = []
        for spec_data in specifications:
            spec_id = spec_data.get('specification_id')
            value = spec_data.get('value')

            if not spec_id or not value:
                continue

            try:
                specification = Specification.objects.get(id=spec_id)
                product_spec = ProductSpecification.objects.create(
                    product=product,
                    specification=specification,
                    specification_value=value
                )
                created_specs.append({
                    'specification_id': str(specification.id),
                    'specification_name': specification.specification_name,
                    'category_id': str(specification.category.id),
                    'category_name': specification.category.category_name,
                    'value': value
                })
            except Specification.DoesNotExist:
                pass

        return Response(created_specs, status=status.HTTP_201_CREATED)
