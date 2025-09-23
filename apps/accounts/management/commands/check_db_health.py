"""
Management command to check database health and connection status
Useful for debugging Neon connection issues
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import time


class Command(BaseCommand):
    help = 'Check database connection health and performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-queries',
            action='store_true',
            help='Run test queries to check performance',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Database Health Check ==='))
        
        # Check basic connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] == 1:
                    self.stdout.write(self.style.SUCCESS('✓ Database connection: OK'))
                else:
                    self.stdout.write(self.style.ERROR('✗ Database connection: FAILED'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Database connection error: {e}'))
            return

        # Check database info
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                self.stdout.write(f'Database version: {version}')
                
                cursor.execute("SELECT current_database()")
                db_name = cursor.fetchone()[0]
                self.stdout.write(f'Database name: {db_name}')
                
                cursor.execute("SELECT current_user")
                user = cursor.fetchone()[0]
                self.stdout.write(f'Database user: {user}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not get database info: {e}'))

        # Check connection settings
        db_settings = settings.DATABASES['default']
        self.stdout.write(f'Connection max age: {db_settings.get("CONN_MAX_AGE", "Not set")}')
        self.stdout.write(f'Atomic requests: {db_settings.get("ATOMIC_REQUESTS", False)}')
        self.stdout.write(f'SSL mode: {db_settings.get("OPTIONS", {}).get("sslmode", "Not set")}')

        # Test queries if requested
        if options['test_queries']:
            self.stdout.write(self.style.SUCCESS('\n=== Running Test Queries ==='))
            
            # Test simple query performance
            start_time = time.time()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM auth_user")
                    user_count = cursor.fetchone()[0]
                    query_time = time.time() - start_time
                    self.stdout.write(f'✓ User count query: {user_count} users ({query_time:.3f}s)')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ User count query failed: {e}'))

            # Test transaction
            start_time = time.time()
            try:
                from django.db import transaction
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        transaction_time = time.time() - start_time
                        self.stdout.write(f'✓ Transaction test: OK ({transaction_time:.3f}s)')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Transaction test failed: {e}'))

        self.stdout.write(self.style.SUCCESS('\n=== Health Check Complete ==='))