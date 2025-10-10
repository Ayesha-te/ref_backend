#!/usr/bin/env python
"""
Initialize Global Pool State
Creates the initial GlobalPoolState record if it doesn't exist
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.earnings.models import GlobalPoolState
from decimal import Decimal

def main():
    print("Initializing Global Pool State...")
    
    # Check if GlobalPoolState already exists
    state = GlobalPoolState.objects.first()
    
    if state:
        print(f"\n✓ GlobalPoolState already exists:")
        print(f"  - Current Pool: ${state.current_pool_usd}")
        print(f"  - Last Collection: {state.last_collection_date or 'Never'}")
        print(f"  - Last Distribution: {state.last_distribution_date or 'Never'}")
        print(f"  - Total Collected (All Time): ${state.total_collected_all_time}")
        print(f"  - Total Distributed (All Time): ${state.total_distributed_all_time}")
    else:
        # Create initial state
        state = GlobalPoolState.objects.create(
            current_pool_usd=Decimal('0.00'),
            last_collection_date=None,
            last_distribution_date=None,
            total_collected_all_time=Decimal('0.00'),
            total_distributed_all_time=Decimal('0.00')
        )
        print(f"\n✓ GlobalPoolState created successfully!")
        print(f"  - Current Pool: ${state.current_pool_usd}")
        print(f"  - Ready for Monday collection and distribution")
    
    print("\n✓ Global Pool System is ready!")

if __name__ == '__main__':
    main()