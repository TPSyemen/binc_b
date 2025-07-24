"""
Management command to calculate AI ratings for products.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core.models import Product, Category, Shop
from core.ai_rating_system import ai_rating_system
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calculate AI ratings for products using the comprehensive rating system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-id',
            type=str,
            help='Calculate rating for a specific product by ID',
        )
        parser.add_argument(
            '--category-id',
            type=str,
            help='Calculate ratings for all products in a specific category',
        )
        parser.add_argument(
            '--shop-id',
            type=str,
            help='Calculate ratings for all products in a specific shop',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Calculate ratings for all active products',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=1000,
            help='Maximum number of products to process (default: 1000)',
        )
        parser.add_argument(
            '--force-recalculate',
            action='store_true',
            help='Force recalculation even if recent ratings exist',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually calculating ratings',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed progress information',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Starting AI rating calculation at {timezone.now()}')
        )

        # Build queryset based on options
        queryset = Product.objects.filter(is_active=True).select_related(
            'shop', 'brand', 'category'
        )
        
        if options['product_id']:
            try:
                product = Product.objects.get(id=options['product_id'], is_active=True)
                products = [product]
                self.stdout.write(f'Processing single product: {product.name}')
            except Product.DoesNotExist:
                raise CommandError(f'Product with ID {options["product_id"]} not found')
        
        elif options['category_id']:
            try:
                category = Category.objects.get(id=options['category_id'])
                products = queryset.filter(category=category)[:options['limit']]
                self.stdout.write(f'Processing products in category: {category.name}')
            except Category.DoesNotExist:
                raise CommandError(f'Category with ID {options["category_id"]} not found')
        
        elif options['shop_id']:
            try:
                shop = Shop.objects.get(id=options['shop_id'])
                products = queryset.filter(shop=shop)[:options['limit']]
                self.stdout.write(f'Processing products in shop: {shop.name}')
            except Shop.DoesNotExist:
                raise CommandError(f'Shop with ID {options["shop_id"]} not found')
        
        elif options['all']:
            products = queryset[:options['limit']]
            self.stdout.write(f'Processing all active products (limit: {options["limit"]})')
        
        else:
            raise CommandError(
                'You must specify one of: --product-id, --category-id, --shop-id, or --all'
            )

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would process {len(products)} products:')
            )
            for product in products[:10]:  # Show first 10
                self.stdout.write(f'  - {product.name} (ID: {product.id})')
            if len(products) > 10:
                self.stdout.write(f'  ... and {len(products) - 10} more products')
            return

        # Process products
        total_products = len(products)
        successful = 0
        failed = 0
        errors = []

        self.stdout.write(f'Processing {total_products} products...')

        for i, product in enumerate(products, 1):
            if options['verbose']:
                self.stdout.write(
                    f'[{i}/{total_products}] Processing: {product.name} (ID: {product.id})'
                )
            elif i % 50 == 0:  # Progress update every 50 products
                self.stdout.write(f'Processed {i}/{total_products} products...')
            
            try:
                rating_data = ai_rating_system.calculate_ai_rating(
                    product, 
                    recalculate=options['force_recalculate']
                )
                
                if 'error' not in rating_data:
                    successful += 1
                    if options['verbose']:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ New rating: {rating_data["overall_rating"]}/5.0 '
                                f'(confidence: {rating_data.get("confidence_level", "N/A")})'
                            )
                        )
                else:
                    failed += 1
                    error_msg = rating_data['error']
                    errors.append(f'Product {product.id}: {error_msg}')
                    if options['verbose']:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Error: {error_msg}')
                        )
                    
            except Exception as e:
                failed += 1
                error_msg = str(e)
                errors.append(f'Product {product.id}: {error_msg}')
                if options['verbose']:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Exception: {error_msg}')
                    )
                logger.error(f'Error processing product {product.id}: {e}', exc_info=True)

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(f'AI Rating Calculation completed at {timezone.now()}')
        self.stdout.write(f'Total products processed: {total_products}')
        self.stdout.write(
            self.style.SUCCESS(f'Successful calculations: {successful}')
        )
        
        if failed > 0:
            self.stdout.write(
                self.style.ERROR(f'Failed calculations: {failed}')
            )
            
            if errors and not options['verbose']:
                self.stdout.write('\nErrors encountered:')
                for error in errors[:10]:  # Show first 10 errors
                    self.stdout.write(f'  - {error}')
                if len(errors) > 10:
                    self.stdout.write(f'  ... and {len(errors) - 10} more errors')
        else:
            self.stdout.write('No failures!')
        
        # Performance statistics
        if successful > 0:
            success_rate = (successful / total_products) * 100
            self.stdout.write(f'Success rate: {success_rate:.1f}%')
        
        if failed > 0:
            self.stdout.write(
                self.style.WARNING(
                    'Check the logs for detailed error information.'
                )
            )
        
        # Recommendations
        if total_products > 0:
            self.stdout.write('\nRecommendations:')
            if success_rate < 90:
                self.stdout.write(
                    '- Review error logs and fix data quality issues'
                )
            if total_products >= options['limit']:
                self.stdout.write(
                    f'- Consider running with higher --limit to process more products'
                )
            self.stdout.write(
                '- Schedule regular rating updates to keep ratings current'
            )
            self.stdout.write(
                '- Monitor rating analytics to track system performance'
            )
