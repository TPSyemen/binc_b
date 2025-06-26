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


# Create a singleton instance
recommendation_service = AIRecommendationService()
