from django.test import TestCase
from core.models import Product
from rest_framework.test import APITestCase
from core.models import Product, Category, User
from rest_framework import status

class ProductModelTest(TestCase):
    def test_product_creation(self):
        product = Product.objects.create(name="Test Product", price=100)
        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.price, 100)

class ProductSearchTest(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics")
        Product.objects.create(name="Laptop", price=1000, category=self.category, is_active=True)
        Product.objects.create(name="Phone", price=500, category=self.category, is_active=True)

    def test_search_by_name(self):
        response = self.client.get('/core/api/products/search/', {'q': 'Laptop'})
        self.assertEqual(len(response.data['products']), 1)

    def test_filter_by_price(self):
        response = self.client.get('/core/api/products/search/', {'min_price': 600})
        self.assertEqual(len(response.data['products']), 1)

class PermissionsTest(APITestCase):
    def test_product_list_access(self):
        response = self.client.get('/core/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # السماح للجميع بالوصول

class AuthenticationTest(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username='admin', password='admin123', user_type='admin')
        self.customer_user = User.objects.create_user(username='customer', password='customer123', user_type='customer')

    def test_admin_access(self):
        response = self.client.post('/auth/token/', {'username': 'admin', 'password': 'admin123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        product_response = self.client.get('/core/api/products/')
        self.assertEqual(product_response.status_code, status.HTTP_200_OK)

    def test_customer_access(self):
        response = self.client.post('/auth/token/', {'username': 'customer', 'password': 'customer123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        product_response = self.client.get('/core/api/products/')
        self.assertEqual(product_response.status_code, status.HTTP_200_OK)