"""
Simple cron-friendly command for Render deployments
This command is designed to be called by Render's cron job service
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.earnings.models import PassiveEarning
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate daily earnings for production deployment (cron-friendly)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show earnings statistics',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        show_stats = options['stats']
        current_time = timezone.now()
        
        if verbose:
            self.stdout.write(f'🚀 Starting daily earnings generation at {current_time}')
        
        try:
            # Generate daily earnings
            call_command('run_daily_earnings')
            
            if show_stats:
                self.show_earnings_stats()
            
            if verbose:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Daily earnings completed at {timezone.now()}')
                )
            else:
                self.stdout.write('✅ Daily earnings generated')
                
        except Exception as e:
            error_msg = f'❌ Error generating daily earnings: {str(e)}'
            self.stdout.write(self.style.ERROR(error_msg))
            logger.error(error_msg)
            raise

    def show_earnings_stats(self):
        """Show current earnings statistics"""
        User = get_user_model()
        
        total_users = User.objects.filter(is_approved=True).count()
        users_with_earnings = User.objects.filter(
            passive_earnings__isnull=False
        ).distinct().count()
        
        total_earnings = PassiveEarning.objects.count()
        
        self.stdout.write(f'📊 Earnings Statistics:')
        self.stdout.write(f'   Approved users: {total_users}')
        self.stdout.write(f'   Users with earnings: {users_with_earnings}')
        self.stdout.write(f'   Total earning records: {total_earnings}')
        
        # Show recent earnings
        recent = PassiveEarning.objects.select_related('user').order_by('-created_at')[:3]
        if recent:
            self.stdout.write(f'📈 Recent earnings:')
            for earning in recent:
                self.stdout.write(
                    f'   {earning.user.username}: Day {earning.day_index} - ${earning.amount_usd}'
                )