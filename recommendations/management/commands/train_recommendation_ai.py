from django.core.management.base import BaseCommand
from recommendations.ai_services import recommendation_service
from reviews.models import Review
from core.models import Product, User
import pandas as pd

class Command(BaseCommand):
    help = 'Train AI recommendation models (collaborative and content-based)'

    def handle(self, *args, **options):
        # إعداد بيانات التفاعل (collaborative)
        print('Preparing collaborative filtering data...')
        reviews = Review.objects.all()
        if not reviews.exists():
            print('No review data found. Skipping collaborative filtering training.')
        else:
            user_item_interactions = pd.DataFrame([
                {'user_id': r.user.id, 'product_id': r.product.id, 'score': r.rating or 1}
                for r in reviews
            ])
            recommendation_service.train_collaborative_filtering(user_item_interactions)
            print('Collaborative filtering model trained.')

        # إعداد بيانات المنتجات (content-based)
        print('Preparing content-based filtering data...')
        products = Product.objects.all()
        if not products.exists():
            print('No product data found. Skipping content-based filtering training.')
        else:
            products_df = pd.DataFrame([
                {
                    'id': p.id,
                    'name': p.name,
                    'description': p.description or '',
                    'category': p.category.name if p.category else '',
                    'brand': p.brand.name if p.brand else ''
                }
                for p in products
            ])
            recommendation_service.train_content_based_filtering(products_df)
            print('Content-based filtering model trained.')

        print('AI recommendation models training complete.')
