"""
Management command to synchronize all store integrations.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from store_integration.services import StoreIntegrationService
from store_integration.models import StoreIntegrationConfig
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Synchronize products from all configured external stores'

    def add_arguments(self, parser):
        parser.add_argument(
            '--shop-id',
            type=str,
            help='Sync only a specific shop by ID',
        )
        parser.add_argument(
            '--platform',
            type=str,
            choices=['shopify', 'woocommerce', 'magento', 'amazon', 'ebay'],
            help='Sync only stores of a specific platform',
        )
        parser.add_argument(
            '--full-sync',
            action='store_true',
            help='Perform full synchronization instead of incremental',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without actually syncing',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Starting store synchronization at {timezone.now()}')
        )

        # Build queryset based on options
        configs = StoreIntegrationConfig.objects.filter(is_active=True)
        
        if options['shop_id']:
            configs = configs.filter(shop_id=options['shop_id'])
            if not configs.exists():
                raise CommandError(f'No active integration found for shop {options["shop_id"]}')
        
        if options['platform']:
            configs = configs.filter(platform=options['platform'])
            if not configs.exists():
                raise CommandError(f'No active integrations found for platform {options["platform"]}')

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would sync {configs.count()} store configurations:')
            )
            for config in configs:
                self.stdout.write(f'  - {config.shop.name} ({config.get_platform_display()})')
            return

        # Perform synchronization
        total_configs = configs.count()
        successful_syncs = 0
        failed_syncs = 0

        for i, config in enumerate(configs, 1):
            self.stdout.write(
                f'[{i}/{total_configs}] Syncing {config.shop.name} ({config.get_platform_display()})...'
            )
            
            try:
                integration = StoreIntegrationService.get_integration(config)
                result = integration.sync_products(full_sync=options['full_sync'])
                
                if result['success']:
                    successful_syncs += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Success: {result["processed"]} processed, '
                            f'{result["created"]} created, {result["updated"]} updated'
                        )
                    )
                    if result.get('errors', 0) > 0:
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠ {result["errors"]} errors occurred')
                        )
                else:
                    failed_syncs += 1
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Failed: {result.get("error", "Unknown error")}')
                    )
                    
            except Exception as e:
                failed_syncs += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Exception: {str(e)}')
                )
                logger.error(f'Sync failed for {config.shop.name}: {e}', exc_info=True)

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Synchronization completed at {timezone.now()}')
        self.stdout.write(f'Total configurations: {total_configs}')
        self.stdout.write(
            self.style.SUCCESS(f'Successful syncs: {successful_syncs}')
        )
        if failed_syncs > 0:
            self.stdout.write(
                self.style.ERROR(f'Failed syncs: {failed_syncs}')
            )
        else:
            self.stdout.write('No failures!')
        
        if failed_syncs > 0:
            self.stdout.write(
                self.style.WARNING(
                    'Check the sync logs in the admin panel for detailed error information.'
                )
            )
