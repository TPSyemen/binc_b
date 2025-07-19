"""
AI Services for Recommendations System
This module provides advanced AI-based recommendation services.
"""
import numpy as np
import pandas as pd
import logging
from django.conf import settings
import os
import pickle

# إعداد المسجل (logger)
logger = logging.getLogger(__name__)


# Optional imports with fallbacks
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.preprocessing import MinMaxScaler
    from scipy.sparse import csr_matrix, vstack
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("scikit-learn not available. Some recommendation features will be limited.")
    SKLEARN_AVAILABLE = False

try:
    from implicit.als import AlternatingLeastSquares
    IMPLICIT_AVAILABLE = True
except ImportError:
    logger.warning("implicit library not available. Collaborative filtering will be limited.")
    IMPLICIT_AVAILABLE = False

try:
    import nltk
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    NLTK_AVAILABLE = True
    # Initialize NLTK resources
    try:
        nltk.data.find('vader_lexicon')
    except LookupError:
        try:
            nltk.download('vader_lexicon')
        except Exception as e:
            logger.warning(f"Could not download NLTK resources: {e}")
            NLTK_AVAILABLE = False
except ImportError:
    logger.warning("NLTK not available. Sentiment analysis will be disabled.")
    NLTK_AVAILABLE = False



# Path for model persistence
MODEL_DIR = os.path.join(settings.BASE_DIR, 'recommendations', 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

class AIRecommendationService:
    """
    Advanced AI-based recommendation service that combines collaborative filtering,
    content-based filtering, and sentiment analysis.
    """

    def __init__(self):
        self.als_model = None
        self.tfidf_vectorizer = None
        # تهيئة القواميس/المصفوفات الافتراضية لتفادي الأخطاء
        self.user_to_idx = {}
        self.product_to_idx = {}
        self.idx_to_product = {}
        self.user_item_matrix = None
        self.content_product_ids = np.array([])
        self.content_features = None

        # Initialize sentiment analyzer if NLTK is available
        if NLTK_AVAILABLE:
            try:
                self.sentiment_analyzer = SentimentIntensityAnalyzer()
            except Exception as e:
                logger.warning(f"Could not initialize SentimentIntensityAnalyzer: {e}")
                self.sentiment_analyzer = None
        else:
            self.sentiment_analyzer = None

        self.load_models()

    def load_models(self):
        """Load pre-trained models if they exist."""
        try:
            als_path = os.path.join(MODEL_DIR, 'als_model.pkl')
            tfidf_path = os.path.join(MODEL_DIR, 'tfidf_vectorizer.pkl')

            if os.path.exists(als_path):
                with open(als_path, 'rb') as f:
                    self.als_model = pickle.load(f)
                logger.info("Loaded ALS model from disk")

            if os.path.exists(tfidf_path):
                with open(tfidf_path, 'rb') as f:
                    self.tfidf_vectorizer = pickle.load(f)
                logger.info("Loaded TF-IDF vectorizer from disk")
        except Exception as e:
            logger.error(f"Error loading models: {e}")

    def save_models(self):
        """Save trained models to disk."""
        try:
            if self.als_model:
                with open(os.path.join(MODEL_DIR, 'als_model.pkl'), 'wb') as f:
                    pickle.dump(self.als_model, f)

            if self.tfidf_vectorizer:
                with open(os.path.join(MODEL_DIR, 'tfidf_vectorizer.pkl'), 'wb') as f:
                    pickle.dump(self.tfidf_vectorizer, f)

            logger.info("Models saved to disk")
        except Exception as e:
            logger.error(f"Error saving models: {e}")

    def train_collaborative_filtering(self, user_item_interactions):
        """
        Train a collaborative filtering model using Alternating Least Squares.

        Args:
            user_item_interactions: DataFrame with columns [user_id, product_id, score]
        """
        # Check if implicit library is available
        if not IMPLICIT_AVAILABLE:
            logger.warning("Cannot train collaborative filtering model: implicit library not available")
            return False

        try:
            # Create user-item matrix
            user_ids = user_item_interactions['user_id'].values
            product_ids = user_item_interactions['product_id'].values
            scores = user_item_interactions['score'].values

            # Get unique IDs for mapping
            unique_users = np.unique(user_ids)
            unique_products = np.unique(product_ids)

            # Create mappings
            user_to_idx = {user: idx for idx, user in enumerate(unique_users)}
            product_to_idx = {product: idx for idx, product in enumerate(unique_products)}

            # Map IDs to indices
            user_indices = np.array([user_to_idx[user] for user in user_ids])
            product_indices = np.array([product_to_idx[product] for product in product_ids])

            # Create sparse matrix
            user_item_matrix = csr_matrix(
                (scores, (user_indices, product_indices)),
                shape=(len(unique_users), len(unique_products))
            )

            # Train ALS model
            self.als_model = AlternatingLeastSquares(
                factors=100,  # Increased from 50 for better representation
                regularization=0.01,
                iterations=20,  # Increased from 15 for better convergence
                calculate_training_loss=True
            )
            self.als_model.fit(user_item_matrix)

            # Save mappings as attributes
            self.user_to_idx = user_to_idx
            self.product_to_idx = product_to_idx
            self.idx_to_product = {idx: product for product, idx in product_to_idx.items()}
            self.user_item_matrix = user_item_matrix

            # Save model
            self.save_models()

            logger.info("Collaborative filtering model trained successfully")
            return True
        except Exception as e:
            logger.error(f"Error training collaborative filtering model: {e}")
            return False

    def train_content_based_filtering(self, products_data):
        """
        Train a content-based filtering model using TF-IDF.

        Args:
            products_data: DataFrame with columns [id, name, description, category, brand, specifications]
        """
        # Check if scikit-learn is available
        if not SKLEARN_AVAILABLE:
            logger.warning("Cannot train content-based filtering model: scikit-learn not available")
            return False

        try:
            # Prepare text data by combining relevant features
            products_data['content'] = products_data.apply(
                lambda row: f"{row['name']} {row['description']} {row['category']} {row['brand']} {row.get('specifications', '')}",
                axis=1
            )

            # Create TF-IDF vectorizer
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2)
            )

            # Fit and transform the data
            self.content_features = self.tfidf_vectorizer.fit_transform(products_data['content'])

            # Save product IDs mapping
            self.content_product_ids = products_data['id'].values

            # Save model
            self.save_models()

            logger.info("Content-based filtering model trained successfully")
            return True
        except Exception as e:
            logger.error(f"Error training content-based filtering model: {e}")
            return False

    def analyze_sentiment(self, reviews_data):
        """
        Analyze sentiment in product reviews.

        Args:
            reviews_data: DataFrame with columns [product_id, user_id, comment, rating]

        Returns:
            DataFrame with sentiment scores added
        """
        try:
            # Check if sentiment analyzer is available
            if not self.sentiment_analyzer or not NLTK_AVAILABLE:
                # Fallback: use rating as sentiment
                reviews_data['sentiment_score'] = reviews_data['rating'].apply(lambda r: (r - 3) / 2)  # Scale to -1 to 1
                reviews_data['sentiment'] = reviews_data['rating'].apply(
                    lambda r: 'positive' if r > 3 else ('negative' if r < 3 else 'neutral')
                )
                reviews_data['consistency'] = 1.0  # Perfect consistency since we're using rating directly
                logger.info("Using ratings as sentiment (NLTK not available)")
                return reviews_data

            # Add sentiment analysis columns
            reviews_data['sentiment_score'] = reviews_data['comment'].apply(
                lambda x: self.sentiment_analyzer.polarity_scores(x)['compound'] if x else 0
            )

            # Classify sentiment
            reviews_data['sentiment'] = reviews_data['sentiment_score'].apply(
                lambda score: 'positive' if score > 0.05 else ('negative' if score < -0.05 else 'neutral')
            )

            # Calculate sentiment consistency with rating
            reviews_data['rating_normalized'] = (reviews_data['rating'] - 1) / 4  # Scale to 0-1
            reviews_data['sentiment_normalized'] = (reviews_data['sentiment_score'] + 1) / 2  # Scale to 0-1
            reviews_data['consistency'] = 1 - abs(reviews_data['rating_normalized'] - reviews_data['sentiment_normalized'])

            logger.info("Sentiment analysis completed successfully")
            return reviews_data
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            # Fallback: use rating as sentiment
            try:
                reviews_data['sentiment_score'] = reviews_data['rating'].apply(lambda r: (r - 3) / 2)  # Scale to -1 to 1
                reviews_data['sentiment'] = reviews_data['rating'].apply(
                    lambda r: 'positive' if r > 3 else ('negative' if r < 3 else 'neutral')
                )
                reviews_data['consistency'] = 1.0
                return reviews_data
            except:
                return reviews_data

    def get_popular_products(self, n=10):
        """
        Fallback: Get most popular products (by interactions or ratings).
        Replace this logic with ORM/database query as needed.
        """
        try:
            # Placeholder: Replace with actual ORM query for most popular products
            # Example: Product.objects.order_by('-num_likes', '-num_reviews')[:n]
            # Here, just return first n product IDs if available
            if hasattr(self, 'product_to_idx'):
                all_products = list(self.product_to_idx.keys())
                return all_products[:n]
            return []
        except Exception as e:
            logger.error(f"Error getting popular products: {e}")
            return []

    def get_random_products(self, n=10):
        """
        Fallback: Get random products if no popular products are available.
        Replace this logic with ORM/database query as needed.
        """
        try:
            import random
            if hasattr(self, 'product_to_idx'):
                all_products = list(self.product_to_idx.keys())
                return random.sample(all_products, min(n, len(all_products)))
            return []
        except Exception as e:
            logger.error(f"Error getting random products: {e}")
            return []

    def get_collaborative_recommendations(self, user_id, n=10):
        """
        Get collaborative filtering recommendations for a user.
        Fallback to popular or random products if not enough recommendations.
        Always return at least one product if only one exists in the system.
        Debug: Log product index and recommendations for troubleshooting.
        """
        try:
            logger.info(f"[DEBUG] product_to_idx: {getattr(self, 'product_to_idx', None)}")
            recommendations = []
            if self.als_model and user_id in self.user_to_idx:
                user_idx = self.user_to_idx[user_id]
                user_vector = self.user_item_matrix[user_idx]
                recs = self.als_model.recommend(
                    user_idx, user_vector, N=n, filter_already_liked_items=True
                )
                recommendations = [self.idx_to_product[idx] for idx, _ in recs]
                logger.info(f"[DEBUG] initial recommendations: {recommendations}")
                # Fallback if not enough recommendations
                if len(recommendations) < n:
                    needed = n - len(recommendations)
                    popular = self.get_popular_products(needed)
                    for pid in popular:
                        if pid not in recommendations:
                            recommendations.append(pid)
                            if len(recommendations) >= n:
                                break
                if len(recommendations) < n:
                    needed = n - len(recommendations)
                    randoms = self.get_random_products(needed)
                    for pid in randoms:
                        if pid not in recommendations:
                            recommendations.append(pid)
                            if len(recommendations) >= n:
                                break
                # إذا كان لا يوجد إلا منتج واحد فقط في النظام، أرجعه دائماً
                if not recommendations and hasattr(self, 'product_to_idx'):
                    all_products = list(self.product_to_idx.keys())
                    if len(all_products) == 1:
                        logger.info(f"[DEBUG] Only one product in system: {all_products[0]}")
                        return all_products * n
                logger.info(f"[DEBUG] final recommendations: {recommendations[:n]}")
                return recommendations[:n]
            else:
                # fallback مباشرة إذا لم يوجد user_id في self.user_to_idx أو لم يتم التدريب
                fallback = self.get_popular_products(n)
                if len(fallback) < n:
                    fallback += self.get_random_products(n - len(fallback))
                if not fallback and hasattr(self, 'product_to_idx'):
                    all_products = list(self.product_to_idx.keys())
                    if len(all_products) == 1:
                        logger.info(f"[DEBUG] Only one product in system (no user): {all_products[0]}")
                        return all_products * n
                logger.info(f"[DEBUG] fallback recommendations (no user): {fallback[:n]}")
                return fallback[:n]
        except Exception as e:
            logger.error(f"Error getting collaborative recommendations: {e}")
            fallback = self.get_popular_products(n)
            if len(fallback) < n:
                fallback += self.get_random_products(n - len(fallback))
            if not fallback and hasattr(self, 'product_to_idx'):
                all_products = list(self.product_to_idx.keys())
                if len(all_products) == 1:
                    logger.info(f"[DEBUG] Only one product in system (exception): {all_products[0]}")
                    return all_products * n
            logger.info(f"[DEBUG] fallback recommendations: {fallback[:n]}")
            return fallback[:n]

    def get_content_based_recommendations(self, product_id, n=10):
        """
        Get content-based recommendations similar to a product.

        Args:
            product_id: The product ID
            n: Number of recommendations to return

        Returns:
            List of recommended product IDs
        """
        try:
            if not self.tfidf_vectorizer:
                return []

            # Find the index of the product
            product_idx = np.where(self.content_product_ids == product_id)[0]
            if len(product_idx) == 0:
                return []

            product_idx = product_idx[0]

            # Get the product's feature vector
            product_vector = self.content_features[product_idx]

            # Calculate similarity with all products
            similarities = cosine_similarity(product_vector, self.content_features).flatten()

            # Get top similar products (excluding the product itself)
            similar_indices = similarities.argsort()[::-1][1:n+1]

            # Convert to product IDs
            similar_products = [self.content_product_ids[idx] for idx in similar_indices]

            return similar_products
        except Exception as e:
            logger.error(f"Error getting content-based recommendations: {e}")
            return []

    def get_hybrid_recommendations(self, user_id, user_viewed_products=None, n=10):
        """
        Get hybrid recommendations combining collaborative and content-based filtering.

        Args:
            user_id: The user ID
            user_viewed_products: List of products the user has viewed
            n: Number of recommendations to return

        Returns:
            List of recommended product IDs
        """
        try:
            # Get collaborative filtering recommendations
            cf_recommendations = self.get_collaborative_recommendations(user_id, n=n)

            # If user has viewed products, get content-based recommendations
            cb_recommendations = []
            if user_viewed_products and len(user_viewed_products) > 0:
                # Get content recommendations for each viewed product
                for product_id in user_viewed_products[-5:]:  # Use last 5 viewed products
                    cb_recs = self.get_content_based_recommendations(product_id, n=3)
                    cb_recommendations.extend(cb_recs)

            # Combine recommendations with weights
            # Give more weight to collaborative filtering if we have enough data
            if len(cf_recommendations) >= n//2:
                final_recommendations = cf_recommendations[:n//2]
                # Add content-based recommendations that aren't already included
                for product_id in cb_recommendations:
                    if product_id not in final_recommendations:
                        final_recommendations.append(product_id)
                        if len(final_recommendations) >= n:
                            break
            else:
                # If we don't have enough collaborative data, rely more on content-based
                final_recommendations = list(set(cf_recommendations + cb_recommendations))[:n]

            return final_recommendations
        except Exception as e:
            logger.error(f"Error getting hybrid recommendations: {e}")
            return []

    def get_personalized_recommendations(self, user_id, user_data=None, n=20):
        """
        Get comprehensive personalized recommendations for a user.
        Always fallback to popular/random products if results are empty.
        """
        try:
            user_data = user_data or {}
            viewed_products = user_data.get('viewed_products', [])

            # Get hybrid recommendations
            hybrid_recs = self.get_hybrid_recommendations(user_id, viewed_products, n=n)
            preferred = hybrid_recs[:10]

            # Get content-based recommendations for products the user liked
            liked_products = user_data.get('liked_products', [])
            liked_recs = []
            for product_id in liked_products:
                similar_products = self.get_content_based_recommendations(product_id, n=3)
                liked_recs.extend(similar_products)
            liked_recs = list(dict.fromkeys(liked_recs))[:10]

            # fallback إذا كانت النتائج فارغة
            if not preferred:
                preferred = self.get_popular_products(10)
                if len(preferred) < 10:
                    preferred += self.get_random_products(10 - len(preferred))
            if not liked_recs:
                liked_recs = self.get_popular_products(10)
                if len(liked_recs) < 10:
                    liked_recs += self.get_random_products(10 - len(liked_recs))

            return {
                'preferred': preferred,
                'liked': liked_recs
            }
        except Exception as e:
            logger.error(f"Error getting personalized recommendations: {e}")
            fallback = self.get_popular_products(10)
            if len(fallback) < 10:
                fallback += self.get_random_products(10 - len(fallback))
            return {'preferred': fallback[:10], 'liked': fallback[:10]}


class EnhancedRecommendationService(AIRecommendationService):
    """
    Enhanced recommendation service with cross-store recommendations and interaction triggers.
    """

    def __init__(self):
        super().__init__()
        self.interaction_weights = {
            'view': 1.0,
            'like': 3.0,
            'dislike': -2.0,
            'add_to_cart': 5.0,
            'purchase': 10.0,
            'review': 7.0,
            'share': 4.0,
            'compare': 2.0
        }

    def trigger_recommendations_on_interaction(self, user_id, product_id, interaction_type, context=None):
        """
        Trigger recommendations based on user interaction with a product.

        Args:
            user_id: ID of the user
            product_id: ID of the product interacted with
            interaction_type: Type of interaction (view, like, add_to_cart, etc.)
            context: Additional context about the interaction

        Returns:
            Dict containing various recommendation types
        """
        try:
            from core.models import Product
            from store_integration.aggregation_services import ProductAggregationService

            # Get the product
            product = Product.objects.select_related('shop', 'brand', 'category').get(id=product_id)

            recommendations = {
                'interaction_type': interaction_type,
                'triggered_by': {
                    'product_id': str(product.id),
                    'product_name': product.name,
                    'shop_name': product.shop.name,
                    'price': float(product.price)
                },
                'recommendations': {}
            }

            # 1. Cross-store recommendations for the same/similar product
            if interaction_type in ['view', 'like', 'add_to_cart']:
                cross_store_recs = self.get_cross_store_recommendations(product)
                recommendations['recommendations']['cross_store'] = cross_store_recs

            # 2. Similar products recommendations
            if interaction_type in ['view', 'like', 'compare']:
                similar_recs = self.get_enhanced_similar_products(product, user_id)
                recommendations['recommendations']['similar_products'] = similar_recs

            # 3. Complementary products (frequently bought together)
            if interaction_type in ['add_to_cart', 'purchase']:
                complementary_recs = self.get_complementary_products(product, user_id)
                recommendations['recommendations']['complementary'] = complementary_recs

            # 4. Alternative products (if user dislikes or compares)
            if interaction_type in ['dislike', 'compare']:
                alternative_recs = self.get_alternative_products(product, user_id)
                recommendations['recommendations']['alternatives'] = alternative_recs

            # 5. Trending products in same category
            if interaction_type in ['view', 'like']:
                trending_recs = self.get_trending_in_category(product.category, user_id)
                recommendations['recommendations']['trending'] = trending_recs

            # 6. Price-based recommendations (better deals)
            if interaction_type in ['view', 'add_to_cart']:
                price_recs = self.get_better_price_recommendations(product)
                recommendations['recommendations']['better_deals'] = price_recs

            # Record the interaction for future recommendations
            self.record_user_interaction(user_id, product_id, interaction_type, context)

            return recommendations

        except Exception as e:
            logger.error(f"Error triggering recommendations for interaction: {e}")
            return {'error': str(e)}

    def get_cross_store_recommendations(self, product):
        """
        Get recommendations for the same product from other stores.
        """
        try:
            from store_integration.aggregation_services import ProductAggregationService

            # Find similar products across stores
            similar_products = ProductAggregationService.find_similar_products(
                product, similarity_threshold=0.8
            )

            # Filter for different stores only
            cross_store_products = [
                sp for sp in similar_products
                if sp['product'].shop != product.shop
            ]

            # Sort by best deals (price and reliability)
            cross_store_products.sort(
                key=lambda x: (x['price_difference'], -x['shop_reliability'])
            )

            recommendations = []
            for sp in cross_store_products[:5]:  # Top 5 recommendations
                rec = {
                    'product_id': str(sp['product'].id),
                    'product_name': sp['product'].name,
                    'shop_name': sp['product'].shop.name,
                    'price': float(sp['product'].price),
                    'original_price': float(sp['product'].original_price) if sp['product'].original_price else None,
                    'price_difference': sp['price_difference'],
                    'price_difference_percentage': sp['price_difference_percentage'],
                    'similarity_score': sp['similarity_score'],
                    'shop_reliability': sp['shop_reliability'],
                    'delivery_days': sp['delivery_days'],
                    'recommendation_reason': self._generate_cross_store_reason(sp, product)
                }
                recommendations.append(rec)

            return recommendations

        except Exception as e:
            logger.error(f"Error getting cross-store recommendations: {e}")
            return []

    def get_enhanced_similar_products(self, product, user_id):
        """
        Get enhanced similar product recommendations considering user preferences.
        """
        try:
            # Get user preferences
            user_preferences = self.get_user_preferences(user_id)

            # Get similar products using content-based filtering
            similar_product_ids = self.get_content_based_recommendations(product.id, n=20)

            if not similar_product_ids:
                return []

            from core.models import Product
            similar_products = Product.objects.filter(
                id__in=similar_product_ids,
                is_active=True
            ).select_related('shop', 'brand', 'category')

            recommendations = []
            for similar_product in similar_products[:10]:
                # Calculate personalized score
                base_score = float(similar_product.rating)

                # Adjust based on user preferences
                if user_preferences.get('preferred_brands') and similar_product.brand:
                    if similar_product.brand.name in user_preferences['preferred_brands']:
                        base_score += 1.0

                if user_preferences.get('price_range'):
                    price_pref = user_preferences['price_range']
                    if price_pref['min'] <= float(similar_product.price) <= price_pref['max']:
                        base_score += 0.5

                # Adjust based on shop reliability
                base_score += (float(similar_product.shop.reliability_score) - 3.0) * 0.2

                rec = {
                    'product_id': str(similar_product.id),
                    'product_name': similar_product.name,
                    'shop_name': similar_product.shop.name,
                    'price': float(similar_product.price),
                    'rating': float(similar_product.rating),
                    'personalized_score': round(base_score, 2),
                    'brand': similar_product.brand.name if similar_product.brand else None,
                    'image_url': similar_product.image_url,
                    'recommendation_reason': f"Similar to {product.name} with {base_score:.1f}/5 personalized score"
                }
                recommendations.append(rec)

            # Sort by personalized score
            recommendations.sort(key=lambda x: x['personalized_score'], reverse=True)

            return recommendations[:8]

        except Exception as e:
            logger.error(f"Error getting enhanced similar products: {e}")
            return []

    def get_complementary_products(self, product, user_id):
        """
        Get products that are frequently bought together with the given product.
        """
        try:
            from core.models import Product
            from django.db.models import Count, Q

            # This is a simplified implementation
            # In a real system, you'd analyze purchase history and order data

            # Get products from the same category that are often viewed together
            complementary_products = Product.objects.filter(
                category=product.category,
                is_active=True
            ).exclude(
                id=product.id
            ).annotate(
                interaction_count=Count('id')  # Simplified metric
            ).order_by('-interaction_count', '-rating')[:8]

            recommendations = []
            for comp_product in complementary_products:
                rec = {
                    'product_id': str(comp_product.id),
                    'product_name': comp_product.name,
                    'shop_name': comp_product.shop.name,
                    'price': float(comp_product.price),
                    'rating': float(comp_product.rating),
                    'category': comp_product.category.name,
                    'image_url': comp_product.image_url,
                    'recommendation_reason': f"Frequently bought with {product.category.name} products"
                }
                recommendations.append(rec)

            return recommendations

        except Exception as e:
            logger.error(f"Error getting complementary products: {e}")
            return []

    def get_alternative_products(self, product, user_id):
        """
        Get alternative products when user shows negative interest or wants to compare.
        """
        try:
            from core.models import Product

            # Get products in same category with different characteristics
            alternatives = Product.objects.filter(
                category=product.category,
                is_active=True
            ).exclude(
                id=product.id
            ).exclude(
                brand=product.brand  # Different brand
            ).order_by('-rating', '-views')[:10]

            recommendations = []
            for alt_product in alternatives:
                # Calculate why it's a good alternative
                reasons = []

                if float(alt_product.price) < float(product.price):
                    savings = float(product.price) - float(alt_product.price)
                    reasons.append(f"Save ${savings:.2f}")

                if float(alt_product.rating) > float(product.rating):
                    reasons.append(f"Higher rated ({alt_product.rating}/5)")

                if alt_product.shop.reliability_score > product.shop.reliability_score:
                    reasons.append("More reliable store")

                if alt_product.shop.average_delivery_days < product.shop.average_delivery_days:
                    reasons.append("Faster delivery")

                rec = {
                    'product_id': str(alt_product.id),
                    'product_name': alt_product.name,
                    'shop_name': alt_product.shop.name,
                    'price': float(alt_product.price),
                    'rating': float(alt_product.rating),
                    'brand': alt_product.brand.name if alt_product.brand else None,
                    'image_url': alt_product.image_url,
                    'advantages': reasons,
                    'recommendation_reason': f"Alternative to {product.name}: {', '.join(reasons[:2])}"
                }
                recommendations.append(rec)

            return recommendations[:6]

        except Exception as e:
            logger.error(f"Error getting alternative products: {e}")
            return []


    def get_trending_in_category(self, category, user_id):
        """
        Get trending products in the same category.
        """
        try:
            from core.models import Product
            from django.utils import timezone
            from datetime import timedelta

            # Get products with high recent activity (views, likes, etc.)
            recent_date = timezone.now() - timedelta(days=7)

            trending_products = Product.objects.filter(
                category=category,
                is_active=True,
                created_at__gte=recent_date  # Recent products
            ).order_by('-views', '-likes', '-rating')[:8]

            # If not enough recent products, get popular ones
            if trending_products.count() < 5:
                popular_products = Product.objects.filter(
                    category=category,
                    is_active=True
                ).order_by('-views', '-rating')[:8]
                trending_products = popular_products

            recommendations = []
            for trending_product in trending_products:
                rec = {
                    'product_id': str(trending_product.id),
                    'product_name': trending_product.name,
                    'shop_name': trending_product.shop.name,
                    'price': float(trending_product.price),
                    'rating': float(trending_product.rating),
                    'views': trending_product.views,
                    'likes': trending_product.likes,
                    'image_url': trending_product.image_url,
                    'recommendation_reason': f"Trending in {category.name}"
                }
                recommendations.append(rec)

            return recommendations

        except Exception as e:
            logger.error(f"Error getting trending products: {e}")
            return []

    def get_better_price_recommendations(self, product):
        """
        Get recommendations for better deals on similar products.
        """
        try:
            from store_integration.models import PriceHistory
            from core.models import Product
            from django.db.models import Min, Avg

            # Find products in same category with better prices
            category_avg_price = Product.objects.filter(
                category=product.category,
                is_active=True
            ).aggregate(avg_price=Avg('price'))['avg_price'] or 0

            better_deals = Product.objects.filter(
                category=product.category,
                is_active=True,
                price__lt=float(product.price) * 0.9  # At least 10% cheaper
            ).order_by('price', '-rating')[:8]

            recommendations = []
            for deal_product in better_deals:
                savings = float(product.price) - float(deal_product.price)
                savings_percentage = (savings / float(product.price)) * 100

                # Check if this is historically a good price
                recent_prices = PriceHistory.objects.filter(
                    product=deal_product
                ).order_by('-recorded_at')[:10]

                is_good_deal = True
                if recent_prices.exists():
                    avg_recent_price = sum(float(p.price) for p in recent_prices) / len(recent_prices)
                    is_good_deal = float(deal_product.price) <= avg_recent_price

                rec = {
                    'product_id': str(deal_product.id),
                    'product_name': deal_product.name,
                    'shop_name': deal_product.shop.name,
                    'price': float(deal_product.price),
                    'original_price': float(deal_product.original_price) if deal_product.original_price else None,
                    'rating': float(deal_product.rating),
                    'savings': round(savings, 2),
                    'savings_percentage': round(savings_percentage, 1),
                    'is_historically_good_deal': is_good_deal,
                    'shop_reliability': float(deal_product.shop.reliability_score),
                    'image_url': deal_product.image_url,
                    'recommendation_reason': f"Save ${savings:.2f} ({savings_percentage:.1f}%) compared to {product.name}"
                }
                recommendations.append(rec)

            return recommendations

        except Exception as e:
            logger.error(f"Error getting better price recommendations: {e}")
            return []

    def record_user_interaction(self, user_id, product_id, interaction_type, context=None):
        """
        Record user interaction for future recommendation improvements.
        """
        try:
            from .models import UserInteraction

            # Get or create interaction record
            interaction, created = UserInteraction.objects.get_or_create(
                user_id=user_id,
                product_id=product_id,
                defaults={
                    'interaction_type': interaction_type,
                    'interaction_count': 1,
                    'context': context or {}
                }
            )

            if not created:
                # Update existing interaction
                interaction.interaction_count += 1
                interaction.last_interaction_type = interaction_type
                interaction.context.update(context or {})
                interaction.save()

            # Update user's interaction weight for this product
            weight = self.interaction_weights.get(interaction_type, 1.0)
            self.update_user_product_weight(user_id, product_id, weight)

        except Exception as e:
            logger.error(f"Error recording user interaction: {e}")

    def update_user_product_weight(self, user_id, product_id, weight_delta):
        """
        Update the weight/score for a user-product pair based on interactions.
        """
        try:
            from .models import UserProductWeight

            weight_record, created = UserProductWeight.objects.get_or_create(
                user_id=user_id,
                product_id=product_id,
                defaults={'weight': weight_delta}
            )

            if not created:
                weight_record.weight += weight_delta
                weight_record.save()

        except Exception as e:
            logger.error(f"Error updating user product weight: {e}")

    def get_user_preferences(self, user_id):
        """
        Get user preferences based on interaction history.
        """
        try:
            from .models import UserInteraction, UserProductWeight
            from core.models import Product
            from django.db.models import Avg, Count

            # Get user's highly weighted products
            top_products = UserProductWeight.objects.filter(
                user_id=user_id,
                weight__gt=5.0  # Significant positive interaction
            ).order_by('-weight')[:20]

            if not top_products.exists():
                return {}

            product_ids = [wp.product_id for wp in top_products]
            products = Product.objects.filter(
                id__in=product_ids
            ).select_related('brand', 'category')

            # Analyze preferences
            preferences = {
                'preferred_brands': [],
                'preferred_categories': [],
                'price_range': {'min': 0, 'max': 1000},
                'preferred_shops': []
            }

            # Brand preferences
            brand_counts = {}
            for product in products:
                if product.brand:
                    brand_counts[product.brand.name] = brand_counts.get(product.brand.name, 0) + 1

            preferences['preferred_brands'] = [
                brand for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ]

            # Category preferences
            category_counts = {}
            for product in products:
                category_counts[product.category.name] = category_counts.get(product.category.name, 0) + 1

            preferences['preferred_categories'] = [
                cat for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ]

            # Price range preferences
            prices = [float(product.price) for product in products]
            if prices:
                preferences['price_range'] = {
                    'min': min(prices) * 0.8,  # 20% below minimum
                    'max': max(prices) * 1.2   # 20% above maximum
                }

            # Shop preferences
            shop_counts = {}
            for product in products:
                shop_counts[product.shop.name] = shop_counts.get(product.shop.name, 0) + 1

            preferences['preferred_shops'] = [
                shop for shop, count in sorted(shop_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ]

            return preferences

        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return {}

    def _generate_cross_store_reason(self, similar_product_data, original_product):
        """
        Generate a human-readable reason for cross-store recommendation.
        """
        reasons = []

        price_diff = similar_product_data['price_difference']
        if price_diff < 0:
            reasons.append(f"Save ${abs(price_diff):.2f}")

        if similar_product_data['shop_reliability'] > original_product.shop.reliability_score:
            reasons.append("More reliable store")

        if similar_product_data['delivery_days'] < original_product.shop.average_delivery_days:
            reasons.append("Faster delivery")

        if similar_product_data['similarity_score'] > 0.9:
            reasons.append("Nearly identical product")

        if not reasons:
            reasons.append("Alternative store option")

        return f"Same product from {similar_product_data['product'].shop.name}: {', '.join(reasons[:2])}"


# Create enhanced singleton instance
recommendation_service = EnhancedRecommendationService()
