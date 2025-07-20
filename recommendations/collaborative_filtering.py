"""
Robust Collaborative Filtering Implementation
Supports multiple backends: implicit, scikit-learn, and numpy fallbacks.
"""

import numpy as np
import pandas as pd
import logging
from typing import List, Tuple, Optional, Dict, Any
from .dependency_manager import dependency_manager

logger = logging.getLogger(__name__)

class CollaborativeFilteringEngine:
    """
    Robust collaborative filtering engine with multiple backend support.
    """
    
    def __init__(self):
        self.model = None
        self.user_to_idx = {}
        self.product_to_idx = {}
        self.idx_to_user = {}
        self.idx_to_product = {}
        self.user_item_matrix = None
        self.backend = self._select_backend()
        
        logger.info(f"🤖 Initialized collaborative filtering with backend: {self.backend}")
    
    def _select_backend(self) -> str:
        """Select the best available backend for collaborative filtering."""
        if dependency_manager.is_available('implicit'):
            return 'implicit'
        elif dependency_manager.is_available('sklearn'):
            return 'sklearn'
        else:
            return 'numpy'
    
    def train(self, user_item_interactions: pd.DataFrame) -> bool:
        """
        Train the collaborative filtering model.
        
        Args:
            user_item_interactions: DataFrame with columns [user_id, product_id, score]
        
        Returns:
            bool: True if training successful, False otherwise
        """
        try:
            logger.info(f"🏋️ Training collaborative filtering model with {len(user_item_interactions)} interactions")
            
            # Prepare data
            if not self._prepare_data(user_item_interactions):
                return False
            
            # Train based on available backend
            if self.backend == 'implicit':
                return self._train_implicit()
            elif self.backend == 'sklearn':
                return self._train_sklearn()
            else:
                return self._train_numpy()
                
        except Exception as e:
            logger.error(f"❌ Error training collaborative filtering model: {e}")
            return False
    
    def _prepare_data(self, interactions: pd.DataFrame) -> bool:
        """Prepare user-item interaction matrix."""
        try:
            # Get unique users and products
            unique_users = interactions['user_id'].unique()
            unique_products = interactions['product_id'].unique()
            
            # Create mappings
            self.user_to_idx = {user: idx for idx, user in enumerate(unique_users)}
            self.product_to_idx = {product: idx for idx, product in enumerate(unique_products)}
            self.idx_to_user = {idx: user for user, idx in self.user_to_idx.items()}
            self.idx_to_product = {idx: product for product, idx in self.product_to_idx.items()}
            
            # Create user-item matrix
            n_users = len(unique_users)
            n_products = len(unique_products)
            
            if dependency_manager.is_available('scipy'):
                from scipy.sparse import csr_matrix
                user_indices = [self.user_to_idx[user] for user in interactions['user_id']]
                product_indices = [self.product_to_idx[product] for product in interactions['product_id']]
                scores = interactions['score'].values
                
                self.user_item_matrix = csr_matrix(
                    (scores, (user_indices, product_indices)),
                    shape=(n_users, n_products)
                )
            else:
                # Fallback to dense numpy matrix
                self.user_item_matrix = np.zeros((n_users, n_products))
                for _, row in interactions.iterrows():
                    user_idx = self.user_to_idx[row['user_id']]
                    product_idx = self.product_to_idx[row['product_id']]
                    self.user_item_matrix[user_idx, product_idx] = row['score']
            
            logger.info(f"📊 Created user-item matrix: {n_users} users × {n_products} products")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error preparing data: {e}")
            return False
    
    def _train_implicit(self) -> bool:
        """Train using implicit library (ALS)."""
        try:
            from implicit.als import AlternatingLeastSquares
            
            self.model = AlternatingLeastSquares(
                factors=100,
                regularization=0.01,
                iterations=20,
                calculate_training_loss=True,
                random_state=42
            )
            
            # implicit expects item-user matrix (transposed)
            if hasattr(self.user_item_matrix, 'T'):
                item_user_matrix = self.user_item_matrix.T
            else:
                item_user_matrix = self.user_item_matrix.T
            
            self.model.fit(item_user_matrix)
            logger.info("✅ Successfully trained implicit ALS model")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error training implicit model: {e}")
            return False
    
    def _train_sklearn(self) -> bool:
        """Train using scikit-learn (SVD + KNN)."""
        try:
            from sklearn.decomposition import TruncatedSVD
            from sklearn.neighbors import NearestNeighbors
            
            # Convert sparse matrix to dense if needed
            if hasattr(self.user_item_matrix, 'toarray'):
                matrix = self.user_item_matrix.toarray()
            else:
                matrix = self.user_item_matrix
            
            # Use SVD for dimensionality reduction
            self.svd_model = TruncatedSVD(n_components=50, random_state=42)
            user_features = self.svd_model.fit_transform(matrix)
            
            # Use KNN for finding similar users
            self.knn_model = NearestNeighbors(n_neighbors=10, metric='cosine')
            self.knn_model.fit(user_features)
            
            self.model = {
                'svd': self.svd_model,
                'knn': self.knn_model,
                'user_features': user_features
            }
            
            logger.info("✅ Successfully trained scikit-learn SVD+KNN model")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error training scikit-learn model: {e}")
            return False
    
    def _train_numpy(self) -> bool:
        """Train using numpy-only implementation (simple similarity)."""
        try:
            # Simple user-based collaborative filtering using cosine similarity
            if hasattr(self.user_item_matrix, 'toarray'):
                matrix = self.user_item_matrix.toarray()
            else:
                matrix = self.user_item_matrix
            
            # Calculate user similarity matrix
            # Normalize rows to unit vectors
            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Avoid division by zero
            normalized_matrix = matrix / norms
            
            # Calculate cosine similarity
            user_similarity = np.dot(normalized_matrix, normalized_matrix.T)
            
            self.model = {
                'user_similarity': user_similarity,
                'user_item_matrix': matrix
            }
            
            logger.info("✅ Successfully trained numpy-based similarity model")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error training numpy model: {e}")
            return False
    
    def get_recommendations(self, user_id: int, n_recommendations: int = 10) -> List[Tuple[int, float]]:
        """
        Get product recommendations for a user.
        
        Args:
            user_id: User ID
            n_recommendations: Number of recommendations to return
        
        Returns:
            List of (product_id, score) tuples
        """
        if self.model is None:
            logger.warning("⚠️ Model not trained. Cannot provide recommendations.")
            return []
        
        if user_id not in self.user_to_idx:
            logger.warning(f"⚠️ User {user_id} not found in training data.")
            return []
        
        try:
            if self.backend == 'implicit':
                return self._get_implicit_recommendations(user_id, n_recommendations)
            elif self.backend == 'sklearn':
                return self._get_sklearn_recommendations(user_id, n_recommendations)
            else:
                return self._get_numpy_recommendations(user_id, n_recommendations)
                
        except Exception as e:
            logger.error(f"❌ Error getting recommendations: {e}")
            return []
    
    def _get_implicit_recommendations(self, user_id: int, n_recommendations: int) -> List[Tuple[int, float]]:
        """Get recommendations using implicit model."""
        user_idx = self.user_to_idx[user_id]
        
        # Get recommendations from implicit model
        product_indices, scores = self.model.recommend(
            user_idx, 
            self.user_item_matrix[user_idx],
            N=n_recommendations,
            filter_already_liked_items=True
        )
        
        # Convert back to product IDs
        recommendations = [
            (self.idx_to_product[product_idx], float(score))
            for product_idx, score in zip(product_indices, scores)
        ]
        
        return recommendations
    
    def _get_sklearn_recommendations(self, user_id: int, n_recommendations: int) -> List[Tuple[int, float]]:
        """Get recommendations using scikit-learn model."""
        user_idx = self.user_to_idx[user_id]
        user_features = self.model['user_features']
        
        # Find similar users
        distances, indices = self.model['knn'].kneighbors([user_features[user_idx]])
        similar_users = indices[0][1:]  # Exclude the user themselves
        
        # Get recommendations based on similar users' preferences
        if hasattr(self.user_item_matrix, 'toarray'):
            matrix = self.user_item_matrix.toarray()
        else:
            matrix = self.user_item_matrix
        
        user_ratings = matrix[user_idx]
        recommendations_scores = np.zeros(matrix.shape[1])
        
        for similar_user_idx in similar_users:
            similar_user_ratings = matrix[similar_user_idx]
            # Weight by similarity (inverse of distance)
            weight = 1.0 / (distances[0][list(similar_users).index(similar_user_idx) + 1] + 1e-8)
            recommendations_scores += weight * similar_user_ratings
        
        # Filter out already rated items
        already_rated = user_ratings > 0
        recommendations_scores[already_rated] = 0
        
        # Get top recommendations
        top_indices = np.argsort(recommendations_scores)[::-1][:n_recommendations]
        
        recommendations = [
            (self.idx_to_product[product_idx], float(recommendations_scores[product_idx]))
            for product_idx in top_indices
            if recommendations_scores[product_idx] > 0
        ]
        
        return recommendations
    
    def _get_numpy_recommendations(self, user_id: int, n_recommendations: int) -> List[Tuple[int, float]]:
        """Get recommendations using numpy-only implementation."""
        user_idx = self.user_to_idx[user_id]
        user_similarity = self.model['user_similarity']
        matrix = self.model['user_item_matrix']
        
        # Find most similar users
        similarities = user_similarity[user_idx]
        similar_user_indices = np.argsort(similarities)[::-1][1:11]  # Top 10 similar users
        
        # Calculate weighted average of similar users' ratings
        user_ratings = matrix[user_idx]
        recommendations_scores = np.zeros(matrix.shape[1])
        
        for similar_user_idx in similar_user_indices:
            if similarities[similar_user_idx] > 0:
                similar_user_ratings = matrix[similar_user_idx]
                recommendations_scores += similarities[similar_user_idx] * similar_user_ratings
        
        # Filter out already rated items
        already_rated = user_ratings > 0
        recommendations_scores[already_rated] = 0
        
        # Get top recommendations
        top_indices = np.argsort(recommendations_scores)[::-1][:n_recommendations]
        
        recommendations = [
            (self.idx_to_product[product_idx], float(recommendations_scores[product_idx]))
            for product_idx in top_indices
            if recommendations_scores[product_idx] > 0
        ]
        
        return recommendations
