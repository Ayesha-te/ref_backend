#!/usr/bin/env python
"""
Backfill Passive Earnings Script
=================================

This script helps you backfill missing passive earnings for existing users.

Usage Examples:
--------------

1. DRY RUN (see what would happen without making changes):
   python backfill_earnings.py --dry-run

2. Backfill from September 22, 2024:
   python backfill_earnings.py --from-date 2024-09-22

3. Backfill last 30 days:
   python backfill_earnings.py --days 30

4. Backfill from specific date (dry run first):
   python backfill_earnings.py --from-date 2024-09-22 --dry-run
   python backfill_earnings.py --from-date 2024-09-22

"""

import os
import sys
import django
import argparse
from datetime import datetime

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.management import call_command

def main():
    parser = argparse.ArgumentParser(
        description='Backfill passive earnings for existing users',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--from-date',
        type=str,
        help='Backfill from specific date (YYYY-MM-DD format, e.g., 2024-09-22)'
    )
    group.add_argument(
        '--days',
        type=int,
        help='Number of days to backfill from today'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("🔄 PASSIVE EARNINGS BACKFILL TOOL")
    print("="*70 + "\n")
    
    if args.dry_run:
        print("⚠️  DRY RUN MODE - No changes will be made\n")
    
    # Build command arguments
    cmd_args = []
    
    if args.from_date:
        # Validate date format
        try:
            datetime.strptime(args.from_date, '%Y-%m-%d')
            cmd_args.extend(['--backfill-from-date', args.from_date])
            print(f"📅 Backfilling from: {args.from_date}")
        except ValueError:
            print("❌ Invalid date format. Use YYYY-MM-DD (e.g., 2024-09-22)")
            sys.exit(1)
    elif args.days:
        cmd_args.extend(['--backfill-days', str(args.days)])
        print(f"📅 Backfilling last {args.days} days")
    
    if args.dry_run:
        cmd_args.append('--dry-run')
    
    print("\n" + "-"*70 + "\n")
    
    # Run the management command
    try:
        call_command('run_daily_earnings', *cmd_args)
        
        if args.dry_run:
            print("\n" + "="*70)
            print("✅ DRY RUN COMPLETE")
            print("="*70)
            print("\nTo apply these changes, run the same command without --dry-run:")
            if args.from_date:
                print(f"  python backfill_earnings.py --from-date {args.from_date}")
            else:
                print(f"  python backfill_earnings.py --days {args.days}")
        else:
            print("\n" + "="*70)
            print("✅ BACKFILL COMPLETE")
            print("="*70)
            print("\nPassive earnings have been successfully added to user accounts!")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()