"""
api/documentation_views.py
--------------------------
API documentation and schema views for frontend developers.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
import json


class APIDocumentationViewSet(viewsets.ViewSet):
    """
    ViewSet providing comprehensive API documentation for frontend developers.
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        Get API overview and general information.
        """
        return Response({
            'api_name': 'E-commerce Aggregation Platform API',
            'version': '1.0.0',
            'description': 'Comprehensive REST API for intelligent e-commerce aggregation platform',
            'base_url': request.build_absolute_uri('/api/'),
            'authentication': {
                'type': 'Token Authentication',
                'header': 'Authorization: Token <your-token>',
                'description': 'Some endpoints require authentication. Include the token in the Authorization header.'
            },
            'rate_limiting': {
                'authenticated': '1000 requests per hour',
                'anonymous': '100 requests per hour'
            },
            'response_format': {
                'success': {
                    'success': True,
                    'data': '...',
                    'message': 'Optional success message'
                },
                'error': {
                    'success': False,
                    'error': 'Error description',
                    'details': 'Optional error details'
                }
            },
            'endpoints': {
                'product_discovery': '/api/frontend/search_products/',
                'product_details': '/api/frontend/product_details/',
                'product_comparison': '/api/frontend/compare_products/',
                'home_feed': '/api/frontend/home_feed/',
                'user_dashboard': '/api/frontend/user_dashboard/',
                'submit_review': '/api/frontend/submit_review/',
                'track_engagement': '/api/frontend/track_engagement/'
            }
        })
    
    @action(detail=False, methods=['get'])
    def product_endpoints(self, request):
        """
        Get documentation for product-related endpoints.
        """
        return Response({
            'product_search': {
                'endpoint': '/api/frontend/search_products/',
                'method': 'GET',
                'description': 'Search products with intelligent filtering and sorting',
                'parameters': {
                    'q': {
                        'type': 'string',
                        'required': False,
                        'description': 'Search query'
                    },
                    'category_id': {
                        'type': 'uuid',
                        'required': False,
                        'description': 'Filter by category'
                    },
                    'brand_id': {
                        'type': 'uuid',
                        'required': False,
                        'description': 'Filter by brand'
                    },
                    'shop_id': {
                        'type': 'uuid',
                        'required': False,
                        'description': 'Filter by shop'
                    },
                    'min_price': {
                        'type': 'float',
                        'required': False,
                        'description': 'Minimum price filter'
                    },
                    'max_price': {
                        'type': 'float',
                        'required': False,
                        'description': 'Maximum price filter'
                    },
                    'min_rating': {
                        'type': 'float',
                        'required': False,
                        'description': 'Minimum rating filter (1-5)'
                    },
                    'sort_by': {
                        'type': 'string',
                        'required': False,
                        'default': 'relevance',
                        'options': ['relevance', 'price_low', 'price_high', 'rating', 'popularity', 'newest'],
                        'description': 'Sort order'
                    },
                    'page': {
                        'type': 'integer',
                        'required': False,
                        'default': 1,
                        'description': 'Page number'
                    },
                    'page_size': {
                        'type': 'integer',
                        'required': False,
                        'default': 20,
                        'max': 100,
                        'description': 'Number of results per page'
                    }
                },
                'response_example': {
                    'success': True,
                    'query': 'laptop',
                    'results': [
                        {
                            'id': 'uuid',
                            'name': 'Product Name',
                            'price': 999.99,
                            'original_price': 1199.99,
                            'discount_percentage': 16.7,
                            'rating': 4.5,
                            'shop': {
                                'id': 'uuid',
                                'name': 'Shop Name'
                            },
                            'image_url': 'https://...',
                            'price_comparison': []
                        }
                    ],
                    'pagination': {
                        'current_page': 1,
                        'total_pages': 10,
                        'total_results': 200,
                        'page_size': 20
                    }
                }
            },
            'product_details': {
                'endpoint': '/api/frontend/product_details/',
                'method': 'GET',
                'description': 'Get comprehensive product details with comparisons and recommendations',
                'parameters': {
                    'product_id': {
                        'type': 'uuid',
                        'required': True,
                        'description': 'Product ID'
                    }
                },
                'response_example': {
                    'success': True,
                    'product': {
                        'id': 'uuid',
                        'name': 'Product Name',
                        'description': 'Product description',
                        'price': 999.99,
                        'rating': 4.5,
                        'ai_rating': {
                            'overall_rating': 4.2,
                            'components': {},
                            'confidence_level': 0.85
                        },
                        'price_trends': {},
                        'similar_products': [],
                        'recent_reviews': []
                    }
                }
            },
            'product_comparison': {
                'endpoint': '/api/frontend/compare_products/',
                'method': 'GET',
                'description': 'Compare multiple products side by side',
                'parameters': {
                    'product_ids': {
                        'type': 'array[uuid]',
                        'required': True,
                        'min_items': 2,
                        'max_items': 5,
                        'description': 'Array of product IDs to compare'
                    }
                },
                'response_example': {
                    'success': True,
                    'products': [],
                    'comparison_insights': [
                        'Best price: Product A at $999.99',
                        'Highest rated: Product B with 4.8/5 stars'
                    ],
                    'total_compared': 3
                }
            }
        })
    
    @action(detail=False, methods=['get'])
    def user_endpoints(self, request):
        """
        Get documentation for user-related endpoints.
        """
        return Response({
            'home_feed': {
                'endpoint': '/api/frontend/home_feed/',
                'method': 'GET',
                'authentication': 'Optional',
                'description': 'Get personalized home feed with trending products and recommendations',
                'response_example': {
                    'success': True,
                    'feed_data': {
                        'trending_products': [],
                        'recommendations': [],
                        'best_deals': [],
                        'featured_categories': [],
                        'platform_stats': {}
                    },
                    'user_authenticated': True
                }
            },
            'user_dashboard': {
                'endpoint': '/api/frontend/user_dashboard/',
                'method': 'GET',
                'authentication': 'Required',
                'description': 'Get user dashboard with activity, reviews, and recommendations',
                'response_example': {
                    'success': True,
                    'user_data': {},
                    'recent_activity': [],
                    'recent_reviews': [],
                    'recommendations': [],
                    'user_statistics': {}
                }
            },
            'submit_review': {
                'endpoint': '/api/frontend/submit_review/',
                'method': 'POST',
                'authentication': 'Required',
                'description': 'Submit a product review with automatic sentiment analysis',
                'request_body': {
                    'product_id': {
                        'type': 'uuid',
                        'required': True,
                        'description': 'Product ID'
                    },
                    'rating': {
                        'type': 'integer',
                        'required': True,
                        'min': 1,
                        'max': 5,
                        'description': 'Product rating'
                    },
                    'title': {
                        'type': 'string',
                        'required': False,
                        'description': 'Review title'
                    },
                    'comment': {
                        'type': 'string',
                        'required': False,
                        'description': 'Review comment'
                    },
                    'pros': {
                        'type': 'string',
                        'required': False,
                        'description': 'Product pros'
                    },
                    'cons': {
                        'type': 'string',
                        'required': False,
                        'description': 'Product cons'
                    }
                },
                'response_example': {
                    'success': True,
                    'review': {
                        'id': 'uuid',
                        'rating': 5,
                        'title': 'Great product!',
                        'sentiment_label': 'positive'
                    },
                    'message': 'Review submitted successfully'
                }
            },
            'track_engagement': {
                'endpoint': '/api/frontend/track_engagement/',
                'method': 'POST',
                'authentication': 'Required',
                'description': 'Track user engagement events',
                'request_body': {
                    'event_type': {
                        'type': 'string',
                        'required': True,
                        'options': ['product_like', 'product_dislike', 'add_to_cart', 'save_product', 'share_product'],
                        'description': 'Type of engagement event'
                    },
                    'product_id': {
                        'type': 'uuid',
                        'required': False,
                        'description': 'Product ID (if applicable)'
                    },
                    'event_data': {
                        'type': 'object',
                        'required': False,
                        'description': 'Additional event data'
                    }
                }
            }
        })
    
    @action(detail=False, methods=['get'])
    def error_codes(self, request):
        """
        Get documentation for API error codes and handling.
        """
        return Response({
            'http_status_codes': {
                '200': 'OK - Request successful',
                '400': 'Bad Request - Invalid parameters or request format',
                '401': 'Unauthorized - Authentication required',
                '403': 'Forbidden - Access denied',
                '404': 'Not Found - Resource not found',
                '429': 'Too Many Requests - Rate limit exceeded',
                '500': 'Internal Server Error - Server error'
            },
            'common_errors': {
                'authentication_required': {
                    'status': 401,
                    'error': 'Authentication required',
                    'solution': 'Include valid authentication token in Authorization header'
                },
                'invalid_product_id': {
                    'status': 404,
                    'error': 'Product not found',
                    'solution': 'Verify the product ID exists and is active'
                },
                'invalid_parameters': {
                    'status': 400,
                    'error': 'Invalid parameter: <parameter_name>',
                    'solution': 'Check parameter format and valid values'
                },
                'rate_limit_exceeded': {
                    'status': 429,
                    'error': 'Rate limit exceeded',
                    'solution': 'Reduce request frequency or authenticate for higher limits'
                }
            },
            'error_handling_best_practices': [
                'Always check the success field in responses',
                'Handle HTTP status codes appropriately',
                'Implement retry logic for 5xx errors',
                'Show user-friendly messages for 4xx errors',
                'Log errors for debugging purposes'
            ]
        })
    
    @action(detail=False, methods=['get'])
    def examples(self, request):
        """
        Get practical API usage examples.
        """
        return Response({
            'javascript_examples': {
                'search_products': '''
// Search for laptops under $1000
fetch('/api/frontend/search_products/?q=laptop&max_price=1000&sort_by=price_low')
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log('Found products:', data.results);
    }
  });
                ''',
                'get_product_details': '''
// Get detailed product information
fetch('/api/frontend/product_details/?product_id=123e4567-e89b-12d3-a456-426614174000')
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log('Product details:', data.product);
    }
  });
                ''',
                'submit_review': '''
// Submit a product review
fetch('/api/frontend/submit_review/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Token your-auth-token'
  },
  body: JSON.stringify({
    product_id: '123e4567-e89b-12d3-a456-426614174000',
    rating: 5,
    title: 'Excellent product!',
    comment: 'Very satisfied with this purchase.'
  })
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log('Review submitted:', data.review);
  }
});
                '''
            },
            'python_examples': {
                'search_products': '''
import requests

# Search for products
response = requests.get('http://api.example.com/api/frontend/search_products/', {
    'q': 'smartphone',
    'min_rating': 4.0,
    'sort_by': 'rating'
})

if response.status_code == 200:
    data = response.json()
    if data['success']:
        print(f"Found {len(data['results'])} products")
                ''',
                'track_engagement': '''
import requests

# Track user engagement
response = requests.post('http://api.example.com/api/frontend/track_engagement/', 
    headers={'Authorization': 'Token your-auth-token'},
    json={
        'event_type': 'product_like',
        'product_id': '123e4567-e89b-12d3-a456-426614174000'
    }
)

if response.status_code == 200:
    print("Engagement tracked successfully")
                '''
            }
        })
