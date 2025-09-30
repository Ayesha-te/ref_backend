#!/usr/bin/env python
"""
Test Admin API Query - Check what the AdminUsersListView actually returns
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, OuterRef, Subquery, Value, DecimalField, CharField
from django.db.models.functions import Coalesce
from apps.wallets.models import DepositRequest
from apps.earnings.models import PassiveEarning

User = get_user_model()

def test_admin_query():
    """Test the exact query from AdminUsersListView."""
    print("🔍 Testing Admin API Query")
    print("=" * 50)
    
    # Replicate the exact query from AdminUsersListView
    latest_dr = DepositRequest.objects.filter(user=OuterRef('pk')).order_by('-created_at')
    users = User.objects.all().annotate(
        rewards_usd=Coalesce(Sum('passive_earnings__amount_usd'), Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))),
        passive_income_usd=Coalesce(Sum('passive_earnings__amount_usd'), Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))),
        bank_name=Subquery(latest_dr.values('bank_name')[:1], output_field=CharField()),
        account_name=Subquery(latest_dr.values('account_name')[:1], output_field=CharField()),
        referrals_count=Count('referrals', distinct=True),
    )
    
    print("Database query results:")
    for user in users[:5]:
        print(f"\n👤 User: {user.username}")
        
        # Get annotated values
        passive_income = getattr(user, 'passive_income_usd', 'NOT_FOUND')
        rewards = getattr(user, 'rewards_usd', 'NOT_FOUND')
        
        print(f"   Passive Income USD: {passive_income}")
        print(f"   Rewards USD: {rewards}")
        
        # Direct count check
        direct_earnings = PassiveEarning.objects.filter(user=user)
        direct_count = direct_earnings.count()
        direct_sum = direct_earnings.aggregate(total=Sum('amount_usd'))['total'] or 0
        print(f"   Direct earnings count: {direct_count}")
        print(f"   Direct earnings sum: ${direct_sum}")
        
        # Test wallet balance
        try:
            wallet = user.wallet
            current_balance = wallet.available_usd
            print(f"   Current balance USD: ${current_balance}")
        except:
            print(f"   Current balance USD: No wallet")

if __name__ == '__main__':
    test_admin_query()