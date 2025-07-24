"""
Dependency Manager for Recommendations System
Handles optional dependencies and provides fallback mechanisms.
"""

import logging
import warnings
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DependencyManager:
    """Manages optional dependencies and provides fallback mechanisms."""
    
    def __init__(self):
        self.available_libraries = {}
        self.fallback_implementations = {}
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check availability of all optional dependencies."""
        
        # Check scikit-learn
        try:
            import sklearn
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            from sklearn.preprocessing import MinMaxScaler
            from sklearn.decomposition import TruncatedSVD
            from sklearn.neighbors import NearestNeighbors
            from sklearn.cluster import KMeans
            self.available_libraries['sklearn'] = {
                'available': True,
                'version': sklearn.__version__,
                'components': ['TfidfVectorizer', 'cosine_similarity', 'MinMaxScaler', 
                              'TruncatedSVD', 'NearestNeighbors', 'KMeans']
            }
            logger.info(f"✅ scikit-learn {sklearn.__version__} available")
        except ImportError as e:
            self.available_libraries['sklearn'] = {'available': False, 'error': str(e)}
            logger.warning("❌ scikit-learn not available. Content-based filtering will be limited.")
        
        # Check scipy
        try:
            import scipy
            from scipy.sparse import csr_matrix, vstack
            import scipy.sparse as sp
            self.available_libraries['scipy'] = {
                'available': True,
                'version': scipy.__version__,
                'components': ['sparse matrices', 'linear algebra']
            }
            logger.info(f"✅ scipy {scipy.__version__} available")
        except ImportError as e:
            self.available_libraries['scipy'] = {'available': False, 'error': str(e)}
            logger.warning("❌ scipy not available. Matrix operations will use numpy fallbacks.")
        
        # Check implicit
        try:
            import implicit
            from implicit.als import AlternatingLeastSquares
            self.available_libraries['implicit'] = {
                'available': True,
                'version': implicit.__version__,
                'components': ['AlternatingLeastSquares', 'BayesianPersonalizedRanking']
            }
            logger.info(f"✅ implicit {implicit.__version__} available")
        except ImportError as e:
            self.available_libraries['implicit'] = {'available': False, 'error': str(e)}
            logger.warning("❌ implicit not available. Using scikit-learn collaborative filtering fallback.")
        
        # Check NLTK
        try:
            import nltk
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            
            # Check for required NLTK data
            required_data = ['vader_lexicon', 'punkt', 'stopwords']
            missing_data = []
            
            for data_name in required_data:
                try:
                    nltk.data.find(f'tokenizers/{data_name}' if data_name in ['punkt'] 
                                  else f'corpora/{data_name}' if data_name in ['stopwords']
                                  else f'sentiment/{data_name}')
                except LookupError:
                    missing_data.append(data_name)
            
            if missing_data:
                logger.info(f"📥 Downloading missing NLTK data: {missing_data}")
                for data_name in missing_data:
                    try:
                        nltk.download(data_name, quiet=True)
                        logger.info(f"✅ Downloaded {data_name}")
                    except Exception as e:
                        logger.warning(f"❌ Failed to download {data_name}: {e}")
            
            self.available_libraries['nltk'] = {
                'available': True,
                'version': nltk.__version__,
                'components': ['SentimentIntensityAnalyzer', 'tokenizers', 'corpora']
            }
            logger.info(f"✅ NLTK {nltk.__version__} available with required data")
            
        except ImportError as e:
            self.available_libraries['nltk'] = {'available': False, 'error': str(e)}
            logger.warning("❌ NLTK not available. Sentiment analysis will be limited.")
        
        # Check numpy (should always be available)
        try:
            import numpy as np
            self.available_libraries['numpy'] = {
                'available': True,
                'version': np.__version__
            }
        except ImportError as e:
            self.available_libraries['numpy'] = {'available': False, 'error': str(e)}
            logger.error("❌ numpy not available. This is a critical dependency!")
    
    def is_available(self, library: str) -> bool:
        """Check if a library is available."""
        return self.available_libraries.get(library, {}).get('available', False)
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get a comprehensive status report of all dependencies."""
        return {
            'summary': {
                'total_libraries': len(self.available_libraries),
                'available': sum(1 for lib in self.available_libraries.values() if lib.get('available')),
                'missing': sum(1 for lib in self.available_libraries.values() if not lib.get('available'))
            },
            'details': self.available_libraries,
            'recommendations': self._get_recommendations()
        }
    
    def _get_recommendations(self) -> Dict[str, str]:
        """Get recommendations for missing dependencies."""
        recommendations = {}
        
        if not self.is_available('sklearn'):
            recommendations['sklearn'] = "Install with: pip install scikit-learn"
        
        if not self.is_available('scipy'):
            recommendations['scipy'] = "Install with: pip install scipy"
        
        if not self.is_available('implicit'):
            recommendations['implicit'] = "Install with: pip install implicit (optional, has scikit-learn fallback)"
        
        if not self.is_available('nltk'):
            recommendations['nltk'] = "Install with: pip install nltk"
        
        return recommendations
    
    def log_status(self):
        """Log the current status of all dependencies."""
        report = self.get_status_report()
        logger.info("🔍 Dependency Status Report:")
        logger.info(f"   Available: {report['summary']['available']}/{report['summary']['total_libraries']}")
        
        for lib_name, lib_info in report['details'].items():
            if lib_info.get('available'):
                version = lib_info.get('version', 'unknown')
                logger.info(f"   ✅ {lib_name} v{version}")
            else:
                logger.warning(f"   ❌ {lib_name} - {lib_info.get('error', 'not available')}")
        
        if report['recommendations']:
            logger.info("💡 Installation recommendations:")
            for lib, cmd in report['recommendations'].items():
                logger.info(f"   {cmd}")


# Global dependency manager instance
dependency_manager = DependencyManager()
