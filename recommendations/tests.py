from django.test import TestCase
from rest_framework.test import APIClient
from core.models import User, Product

class RecommendationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

        # إنشاء منتجات
        Product.objects.create(name="Product 1", price=100, likes=10)
        Product.objects.create(name="Product 2", price=200, likes=20)

    def test_recommendations(self):
        response = self.client.get('/bincai/recommendations/')
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
