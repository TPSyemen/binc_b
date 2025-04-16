from django.test import TestCase
from promotions.models import Promotion, DiscountCode
from core.models import Product

class PromotionTests(TestCase):
    def setUp(self):
        self.promotion = Promotion.objects.create(
            name="Test Promotion",
            description="Test Description",
            end_date="2025-12-31"
        )
        self.product = Product.objects.create(name="Test Product", price=100)
        self.discount_code = DiscountCode.objects.create(
            code="TEST10",
            discount_percentage=10,
            promotion=self.promotion,
            product=self.product
        )

    def test_promotion_creation(self):
        self.assertEqual(self.promotion.name, "Test Promotion")

    def test_discount_code_creation(self):
        self.assertEqual(self.discount_code.code, "TEST10")
        self.assertEqual(self.discount_code.discount_percentage, 10)

    def test_discount_code_usage_limit(self):
        self.discount_code.used_count = self.discount_code.max_uses
        self.discount_code.save()
        self.assertTrue(self.discount_code.used_count >= self.discount_code.max_uses)
