"""
Management command to set up periodic synchronization tasks.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from store_integration.models import StoreIntegrationConfig
from store_integration.tasks import sync_store_products, monitor_price_changes
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Set up periodic synchronization tasks for store integrations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--config-id',
            type=str,
            help='Set up sync for a specific integration config',
        )
        parser.add_argument(
            '--frequency',
            type=str,
            choices=['hourly', 'daily', 'weekly'],
            help='Override sync frequency for specified config',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be set up without actually creating tasks',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force setup even if tasks already exist',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Setting up periodic sync tasks at {timezone.now()}')
        )

        # Get integration configs to set up
        if options['config_id']:
            try:
                configs = [StoreIntegrationConfig.objects.get(
                    id=options['config_id'], 
                    is_active=True
                )]
                self.stdout.write(f'Setting up sync for specific config: {configs[0].shop.name}')
            except StoreIntegrationConfig.DoesNotExist:
                raise CommandError(f'Integration config {options["config_id"]} not found or inactive')
        else:
            configs = StoreIntegrationConfig.objects.filter(is_active=True)
            self.stdout.write(f'Setting up sync for {configs.count()} active integrations')

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN: No actual tasks will be created')
            )

        setup_count = 0
        skipped_count = 0
        error_count = 0

        for config in configs:
            try:
                # Determine sync frequency
                frequency = options.get('frequency') or config.sync_frequency
                
                if frequency == 'manual':
                    self.stdout.write(f'Skipping {config.shop.name}: Manual sync only')
                    skipped_count += 1
                    continue

                # Check if we should set up this config
                if not options['force'] and self._has_existing_tasks(config):
                    self.stdout.write(f'Skipping {config.shop.name}: Tasks already exist (use --force to override)')
                    skipped_count += 1
                    continue

                if not options['dry_run']:
                    # Set up periodic sync task
                    self._setup_periodic_task(config, frequency)
                    
                    # Set up price monitoring task
                    self._setup_price_monitoring(config)

                self.stdout.write(
                    self.style.SUCCESS(f'✓ Set up periodic sync for {config.shop.name} ({frequency})')
                )
                setup_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error setting up {config.shop.name}: {e}')
                )
                error_count += 1
                logger.error(f'Error setting up periodic sync for {config.id}: {e}')

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(f'Periodic sync setup completed at {timezone.now()}')
        self.stdout.write(f'Configurations processed: {len(configs)}')
        self.stdout.write(
            self.style.SUCCESS(f'Successfully set up: {setup_count}')
        )
        
        if skipped_count > 0:
            self.stdout.write(f'Skipped: {skipped_count}')
        
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'Errors: {error_count}')
            )

        if not options['dry_run'] and setup_count > 0:
            self.stdout.write('\nNext steps:')
            self.stdout.write('1. Ensure Celery workers are running')
            self.stdout.write('2. Ensure Celery beat scheduler is running')
            self.stdout.write('3. Monitor sync logs for any issues')

    def _has_existing_tasks(self, config):
        """
        Check if periodic tasks already exist for this config.
        This is a placeholder - in a real implementation, you'd check
        your task scheduler (Celery Beat, Django-Celery-Beat, etc.)
        """
        # For now, just check if the config has been synced recently
        if config.last_sync_at:
            from datetime import timedelta
            recent_threshold = timezone.now() - timedelta(hours=1)
            return config.last_sync_at > recent_threshold
        return False

    def _setup_periodic_task(self, config, frequency):
        """
        Set up periodic synchronization task.
        """
        try:
            # This would integrate with your task scheduler
            # For example, with django-celery-beat:
            
            from django_celery_beat.models import PeriodicTask, IntervalSchedule
            import json
            
            # Create or get interval schedule
            if frequency == 'hourly':
                schedule, created = IntervalSchedule.objects.get_or_create(
                    every=1,
                    period=IntervalSchedule.HOURS,
                )
            elif frequency == 'daily':
                schedule, created = IntervalSchedule.objects.get_or_create(
                    every=1,
                    period=IntervalSchedule.DAYS,
                )
            elif frequency == 'weekly':
                schedule, created = IntervalSchedule.objects.get_or_create(
                    every=7,
                    period=IntervalSchedule.DAYS,
                )
            else:
                raise ValueError(f'Unsupported frequency: {frequency}')

            # Create or update periodic task
            task_name = f'sync_store_{config.id}'
            task, created = PeriodicTask.objects.get_or_create(
                name=task_name,
                defaults={
                    'task': 'store_integration.tasks.sync_store_products',
                    'interval': schedule,
                    'args': json.dumps([str(config.id), 'scheduled']),
                    'enabled': True,
                }
            )
            
            if not created:
                # Update existing task
                task.interval = schedule
                task.args = json.dumps([str(config.id), 'scheduled'])
                task.enabled = True
                task.save()

            self.stdout.write(f'  Created/updated periodic task: {task_name}')

        except ImportError:
            # Fallback if django-celery-beat is not installed
            self.stdout.write(
                self.style.WARNING(
                    f'  django-celery-beat not available. '
                    f'Manual task scheduling required for {config.shop.name}'
                )
            )
        except Exception as e:
            raise Exception(f'Failed to set up periodic task: {e}')

    def _setup_price_monitoring(self, config):
        """
        Set up price monitoring task.
        """
        try:
            from django_celery_beat.models import PeriodicTask, IntervalSchedule
            import json
            
            # Create interval for price monitoring (every 30 minutes)
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=30,
                period=IntervalSchedule.MINUTES,
            )

            # Create or update price monitoring task
            task_name = f'monitor_prices_{config.id}'
            task, created = PeriodicTask.objects.get_or_create(
                name=task_name,
                defaults={
                    'task': 'store_integration.tasks.monitor_price_changes',
                    'interval': schedule,
                    'args': json.dumps([str(config.id)]),
                    'enabled': True,
                }
            )
            
            if not created:
                # Update existing task
                task.interval = schedule
                task.args = json.dumps([str(config.id)])
                task.enabled = True
                task.save()

            self.stdout.write(f'  Created/updated price monitoring task: {task_name}')

        except ImportError:
            # Fallback if django-celery-beat is not available
            pass
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'  Failed to set up price monitoring: {e}')
            )

    def _cleanup_old_tasks(self, config):
        """
        Clean up old/orphaned periodic tasks for a config.
        """
        try:
            from django_celery_beat.models import PeriodicTask
            
            # Find and disable old tasks
            old_tasks = PeriodicTask.objects.filter(
                name__contains=str(config.id),
                enabled=True
            )
            
            for task in old_tasks:
                task.enabled = False
                task.save()
                self.stdout.write(f'  Disabled old task: {task.name}')

        except ImportError:
            pass
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'  Failed to cleanup old tasks: {e}')
            )
