"""
Cleanup script to remove premature passive income transactions
that were generated on the same day as the deposit (day 0).

This script will:
1. Find all users with passive income transactions
2. Check if they received passive income on day 0 (same day as deposit)
3. Remove those premature transactions
4. Adjust wallet balances accordingly
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, Transaction, DepositRequest
from apps.earnings.models import PassiveEarning
from decimal import Decimal
from django.utils import timezone

User = get_user_model()

def cleanup_premature_passive_income():
    print("=" * 80)
    print("CLEANUP: Premature Passive Income Transactions")
    print("=" * 80)
    
    users_affected = 0
    transactions_removed = 0
    earnings_removed = 0
    total_amount_reversed = Decimal('0.00')
    
    # Get all approved users
    users = User.objects.filter(is_approved=True)
    
    for user in users:
        # Get first credited deposit (excluding signup)
        first_dep = DepositRequest.objects.filter(
            user=user, 
            status='CREDITED'
        ).exclude(tx_id='SIGNUP-INIT').order_by('processed_at', 'created_at').first()
        
        if not first_dep:
            continue
        
        deposit_date = first_dep.processed_at or first_dep.created_at
        if not deposit_date:
            continue
        
        # Get all passive earnings for this user
        passive_earnings = PassiveEarning.objects.filter(user=user).order_by('day_index')
        
        if not passive_earnings.exists():
            continue
        
        # Check if any earnings were created on day 0 (same day as deposit)
        premature_earnings = []
        
        for earning in passive_earnings:
            # Calculate when this earning should have been created
            # Day 1 should be created 1 day after deposit, day 2 should be 2 days after, etc.
            expected_creation_date = deposit_date + timezone.timedelta(days=earning.day_index)
            
            # If the earning was created before the expected date, it's premature
            # Allow a 12-hour buffer for timezone differences
            if earning.created_at < (expected_creation_date - timezone.timedelta(hours=12)):
                premature_earnings.append(earning)
        
        if not premature_earnings:
            continue
        
        print(f"\n{'='*80}")
        print(f"User: {user.username} (ID: {user.id})")
        print(f"Deposit Date: {deposit_date}")
        print(f"Premature Earnings Found: {len(premature_earnings)}")
        print(f"{'='*80}")
        
        wallet = Wallet.objects.get(user=user)
        user_amount_reversed = Decimal('0.00')
        
        for earning in premature_earnings:
            print(f"\n  ❌ Removing premature earning:")
            print(f"     Day Index: {earning.day_index}")
            print(f"     Amount: ${earning.amount_usd}")
            print(f"     Created: {earning.created_at}")
            print(f"     Expected After: {deposit_date + timezone.timedelta(days=earning.day_index)}")
            
            # Find and remove corresponding transaction
            transactions = Transaction.objects.filter(
                wallet=wallet,
                type=Transaction.CREDIT,
                amount_usd=earning.amount_usd,
                meta__type='passive',
                meta__day_index=earning.day_index
            )
            
            for txn in transactions:
                print(f"     Removing transaction ID: {txn.id}")
                user_amount_reversed += txn.amount_usd
                transactions_removed += 1
                txn.delete()
            
            # Remove the earning record
            earnings_removed += 1
            earning.delete()
        
        # Adjust wallet balance
        if user_amount_reversed > 0:
            print(f"\n  💰 Adjusting wallet balance:")
            print(f"     Previous income_usd: ${wallet.income_usd}")
            wallet.income_usd = (Decimal(wallet.income_usd) - user_amount_reversed).quantize(Decimal('0.01'))
            print(f"     New income_usd: ${wallet.income_usd}")
            wallet.save()
            
            users_affected += 1
            total_amount_reversed += user_amount_reversed
    
    # Summary
    print("\n" + "=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    print(f"👥 Users Affected: {users_affected}")
    print(f"📊 Earnings Removed: {earnings_removed}")
    print(f"💳 Transactions Removed: {transactions_removed}")
    print(f"💵 Total Amount Reversed: ${total_amount_reversed}")
    print(f"💵 Total Amount Reversed (PKR): ₨{float(total_amount_reversed) * 280:,.2f}")
    print("=" * 80)
    
    if users_affected > 0:
        print("\n✅ Cleanup completed successfully!")
        print("⚠️  Note: Users will now receive passive income starting from day 1 onwards")
        print("⚠️  The scheduler will generate correct earnings on the next run")
    else:
        print("\n✅ No premature passive income found - system is clean!")

if __name__ == '__main__':
    cleanup_premature_passive_income()