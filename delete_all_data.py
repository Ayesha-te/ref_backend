"""
Script to delete ALL data from the PostgreSQL database.
This will remove all users, transactions, earnings, and related data.
Database structure (tables) will remain intact.
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_4EHeKmWoMTt8@ep-morning-meadow-agkfmyax-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require'

django.setup()

from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, Transaction, DepositRequest
from apps.earnings.models import PassiveEarning, DailyEarningsState
from apps.earnings.models_global_pool import GlobalPool, GlobalPoolPayout
from apps.referrals.models import ReferralPayout, ReferralMilestoneProgress, ReferralMilestoneAward
from apps.withdrawals.models import WithdrawalRequest
from apps.marketplace.models import Product, Order
from apps.accounts.models import SignupProof
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.contrib.sessions.models import Session

User = get_user_model()

def delete_all_data():
    """Delete all data from all tables"""
    
    print("=" * 80)
    print("WARNING: This will DELETE ALL DATA from the database!")
    print("=" * 80)
    print("\nDatabase: Neon PostgreSQL")
    print("URL: ep-morning-meadow-agkfmyax-pooler.c-2.eu-central-1.aws.neon.tech")
    print("\nThis action will:")
    print("  - Delete ALL users")
    print("  - Delete ALL wallets and transactions")
    print("  - Delete ALL earnings records")
    print("  - Delete ALL referral data")
    print("  - Delete ALL withdrawal requests")
    print("  - Delete ALL marketplace products and orders")
    print("  - Delete ALL signup proofs")
    print("  - Delete ALL sessions and tokens")
    print("  - Reset global pool")
    print("\nDatabase tables will remain (structure intact).")
    print("=" * 80)
    
    confirmation = input("\nType 'DELETE ALL' to confirm: ")
    
    if confirmation != "DELETE ALL":
        print("\n❌ Deletion cancelled. No data was deleted.")
        return
    
    print("\n🔥 Starting deletion process...\n")
    
    try:
        # Delete in order to respect foreign key constraints
        
        # 1. JWT Tokens
        print("Deleting JWT tokens...")
        blacklisted_count = BlacklistedToken.objects.all().count()
        BlacklistedToken.objects.all().delete()
        outstanding_count = OutstandingToken.objects.all().count()
        OutstandingToken.objects.all().delete()
        print(f"  ✓ Deleted {blacklisted_count} blacklisted tokens")
        print(f"  ✓ Deleted {outstanding_count} outstanding tokens")
        
        # 2. Sessions
        print("\nDeleting sessions...")
        session_count = Session.objects.all().count()
        Session.objects.all().delete()
        print(f"  ✓ Deleted {session_count} sessions")
        
        # 3. Marketplace Orders
        print("\nDeleting marketplace orders...")
        order_count = Order.objects.all().count()
        Order.objects.all().delete()
        print(f"  ✓ Deleted {order_count} orders")
        
        # 4. Marketplace Products
        print("\nDeleting marketplace products...")
        product_count = Product.objects.all().count()
        Product.objects.all().delete()
        print(f"  ✓ Deleted {product_count} products")
        
        # 5. Withdrawal Requests
        print("\nDeleting withdrawal requests...")
        withdrawal_count = WithdrawalRequest.objects.all().count()
        WithdrawalRequest.objects.all().delete()
        print(f"  ✓ Deleted {withdrawal_count} withdrawal requests")
        
        # 6. Referral Data
        print("\nDeleting referral data...")
        milestone_award_count = ReferralMilestoneAward.objects.all().count()
        ReferralMilestoneAward.objects.all().delete()
        print(f"  ✓ Deleted {milestone_award_count} milestone awards")
        
        milestone_progress_count = ReferralMilestoneProgress.objects.all().count()
        ReferralMilestoneProgress.objects.all().delete()
        print(f"  ✓ Deleted {milestone_progress_count} milestone progress records")
        
        referral_payout_count = ReferralPayout.objects.all().count()
        ReferralPayout.objects.all().delete()
        print(f"  ✓ Deleted {referral_payout_count} referral payouts")
        
        # 7. Global Pool
        print("\nDeleting global pool data...")
        pool_payout_count = GlobalPoolPayout.objects.all().count()
        GlobalPoolPayout.objects.all().delete()
        print(f"  ✓ Deleted {pool_payout_count} global pool payouts")
        
        pool_count = GlobalPool.objects.all().count()
        GlobalPool.objects.all().delete()
        print(f"  ✓ Deleted {pool_count} global pool records")
        
        # 8. Earnings
        print("\nDeleting earnings data...")
        earnings_state_count = DailyEarningsState.objects.all().count()
        DailyEarningsState.objects.all().delete()
        print(f"  ✓ Deleted {earnings_state_count} daily earnings state records")
        
        passive_earning_count = PassiveEarning.objects.all().count()
        PassiveEarning.objects.all().delete()
        print(f"  ✓ Deleted {passive_earning_count} passive earnings")
        
        # 9. Wallet Transactions
        print("\nDeleting wallet transactions...")
        transaction_count = Transaction.objects.all().count()
        Transaction.objects.all().delete()
        print(f"  ✓ Deleted {transaction_count} transactions")
        
        # 10. Deposit Requests
        print("\nDeleting deposit requests...")
        deposit_count = DepositRequest.objects.all().count()
        DepositRequest.objects.all().delete()
        print(f"  ✓ Deleted {deposit_count} deposit requests")
        
        # 11. Wallets
        print("\nDeleting wallets...")
        wallet_count = Wallet.objects.all().count()
        Wallet.objects.all().delete()
        print(f"  ✓ Deleted {wallet_count} wallets")
        
        # 12. Signup Proofs
        print("\nDeleting signup proofs...")
        signup_proof_count = SignupProof.objects.all().count()
        SignupProof.objects.all().delete()
        print(f"  ✓ Deleted {signup_proof_count} signup proofs")
        
        # 13. Users (this will cascade delete any remaining related data)
        print("\nDeleting users...")
        user_count = User.objects.all().count()
        User.objects.all().delete()
        print(f"  ✓ Deleted {user_count} users")
        
        print("\n" + "=" * 80)
        print("✅ ALL DATA HAS BEEN DELETED SUCCESSFULLY!")
        print("=" * 80)
        print("\nSummary:")
        print(f"  • {user_count} users deleted")
        print(f"  • {wallet_count} wallets deleted")
        print(f"  • {transaction_count} transactions deleted")
        print(f"  • {deposit_count} deposit requests deleted")
        print(f"  • {passive_earning_count} passive earnings deleted")
        print(f"  • {referral_payout_count} referral payouts deleted")
        print(f"  • {withdrawal_count} withdrawal requests deleted")
        print(f"  • {product_count} products deleted")
        print(f"  • {order_count} orders deleted")
        print(f"  • {signup_proof_count} signup proofs deleted")
        print(f"  • {session_count} sessions deleted")
        print(f"  • {outstanding_count + blacklisted_count} tokens deleted")
        print("\nThe database is now empty and ready for fresh data.")
        print("All tables and structure remain intact.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nDeletion process failed. Some data may have been deleted.")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    delete_all_data()