from django.core.management.base import BaseCommand
from recommendations.ai_services import recommendation_service
from reviews.models import Review
from core.models import Product, User, UserProductReaction
import pandas as pd

class Command(BaseCommand):
    help = 'Train AI recommendation models (collaborative and content-based)'

    def handle(self, *args, **options):
        # إعداد بيانات التفاعل (collaborative)
        print('Preparing collaborative filtering data...')
        reviews = Review.objects.all()
        reactions = UserProductReaction.objects.all()
        user_item_interactions = []
        # أضف بيانات المراجعات (كالعادة)
        for r in reviews:
            user_item_interactions.append({
                'user_id': r.user.id,
                'product_id': r.product.id,
                'score': r.rating or 1
            })
        # أضف بيانات التفاعل (الإعجاب/عدم الإعجاب/محايد/مشاهدة)
        reaction_score_map = {
            'like': 5,
            'dislike': 1,
            'neutral': 3,
            'view': 2
        }
        for react in reactions:
            user_item_interactions.append({
                'user_id': react.user.id,
                'product_id': react.product.id,
                'score': reaction_score_map.get(react.reaction_type, 3)
            })
        if not user_item_interactions:
            print('No review or reaction data found. Skipping collaborative filtering training.')
        else:
            user_item_interactions_df = pd.DataFrame(user_item_interactions)
            recommendation_service.train_collaborative_filtering(user_item_interactions_df)
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
