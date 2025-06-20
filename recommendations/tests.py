from django.test import TestCase
from rest_framework.test import APIClient
from core.models import User, Product, Category, Brand, Shop, Owner

class RecommendationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

        # إنشاء تصنيف وعلامة تجارية ومتجر افتراضي
        category = Category.objects.create(name="Test Category")
        brand = Brand.objects.create(name="Test Brand", popularity=50, rating=3)
        owner = Owner.objects.create(user=self.user, email="owner@email.com", password="testpass")
        shop = Shop.objects.create(name="Test Shop", owner=owner, address="Test Address")

        # إنشاء منتجات
        Product.objects.create(name="Product 1", price=100, likes=10, rating=0, category=category, brand=brand, shop=shop)
        Product.objects.create(name="Product 2", price=200, likes=20, rating=0, category=category, brand=brand, shop=shop)

    def test_recommendations(self):
        response = self.client.get('/api/recommendations/')
        self.assertEqual(response.status_code, 200)

        # Validate response structure
        self.assertIn('preferred', response.data)
        self.assertIn('liked', response.data)
        self.assertIn('new', response.data)
        self.assertIn('popular', response.data)

        # Validate each category contains a list
        self.assertIsInstance(response.data['preferred'], list)
        self.assertIsInstance(response.data['liked'], list)
        self.assertIsInstance(response.data['new'], list)
        self.assertIsInstance(response.data['popular'], list)
