from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Automatic daily task runner - generates earnings and handles all daily operations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        current_time = timezone.now()
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting automated daily tasks at {current_time}')
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No actual changes will be made'))
            return
        
        try:
            # Generate daily earnings (includes global pool logic for Mondays)
            self.stdout.write('Generating daily earnings...')
            call_command('run_daily_earnings')
            self.stdout.write(self.style.SUCCESS('✅ Daily earnings generated successfully'))
            
            # Log completion
            self.stdout.write(
                self.style.SUCCESS(f'Automated daily tasks completed at {timezone.now()}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during automated daily tasks: {str(e)}')
            )
            logger.error(f'Automated daily tasks failed: {str(e)}')
            raise