# PostgreSQL JSONB Query Fix for Income Calculation

## Problem Summary

The `get_current_income_usd()` method in `apps/wallets/models.py` is returning incorrect values (-$0.60 instead of $1.76) for user "sardarlaeiq3@gmail.com" because the PostgreSQL JSONB queries are not matching transactions correctly.

## Root Cause

The Django ORM queries using `Q(meta__type='referral')` are generating SQL like:
```sql
(meta -> 'type') = '"referral"'::jsonb
```

However, this may not be matching the actual JSONB data stored in PostgreSQL due to:
1. JSON string escaping issues
2. JSONB operator compatibility
3. Data type mismatches

## Solution Approach

We need to test different JSONB query approaches to find which one works correctly with PostgreSQL.

## Steps to Fix

### Step 1: Run Diagnostic Script

Run the diagnostic script against the production database:

```powershell
# Set the DATABASE_URL environment variable
$env:DATABASE_URL = "YOUR_PRODUCTION_DATABASE_URL_HERE"

# Run the diagnostic script
python "c:\Users\Ayesha Jahangir\Downloads\nexocart-redline-dash\ref_backend\test_jsonb_query.py"
```

### Step 2: Analyze Results

The script will test 5 different approaches:
1. `Q(meta__type='referral')` - Current approach
2. `meta__contains={'type': 'referral'}` - Contains operator
3. `meta__has_key='type'` + Python filter - Hybrid approach
4. Raw SQL with `meta->>'type'` - Direct PostgreSQL
5. Database inspection - Check actual JSONB storage format

### Step 3: Update the Model

Based on the working approach, update `apps/wallets/models.py` with the correct query syntax.

## Possible Fixes

### Option A: Use `__contains` operator

```python
def get_current_income_usd(self):
    """Calculate total current income from transactions"""
    from django.db.models import Sum, Q
    
    # Use contains instead of direct equality
    income_credits = self.transactions.filter(
        type=Transaction.CREDIT
    ).filter(
        Q(meta__contains={'type': 'passive'}) | 
        Q(meta__contains={'type': 'referral'}) | 
        Q(meta__contains={'type': 'milestone'}) |
        Q(meta__contains={'type': 'global_pool'}) |
        Q(meta__contains={'type': 'referral_correction'})
    ).exclude(
        meta__contains={'source': 'signup-initial'}
    ).exclude(
        meta__contains={'non_income': True}
    ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
    
    income_debits = self.transactions.filter(
        type=Transaction.DEBIT
    ).filter(
        Q(meta__contains={'type': 'withdrawal'}) |
        Q(meta__contains={'type': 'referral_reversal'})
    ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
    
    return (income_credits - income_debits).quantize(Decimal('0.01'))
```

### Option B: Use raw SQL with `->>`

```python
def get_current_income_usd(self):
    """Calculate total current income from transactions"""
    from django.db.models import Sum, Q
    from django.db.models import F
    
    # Use ->> operator for text extraction
    income_credits = self.transactions.filter(
        type=Transaction.CREDIT
    ).extra(
        where=[
            "meta->>'type' IN ('passive', 'referral', 'milestone', 'global_pool', 'referral_correction')",
            "COALESCE(meta->>'source', '') != 'signup-initial'",
            "COALESCE((meta->>'non_income')::boolean, false) = false"
        ]
    ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
    
    income_debits = self.transactions.filter(
        type=Transaction.DEBIT
    ).extra(
        where=["meta->>'type' IN ('withdrawal', 'referral_reversal')"]
    ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
    
    return (income_credits - income_debits).quantize(Decimal('0.01'))
```

### Option C: Hybrid approach (fetch and filter in Python)

```python
def get_current_income_usd(self):
    """Calculate total current income from transactions"""
    from decimal import Decimal
    
    credits = Decimal('0')
    debits = Decimal('0')
    
    # Fetch all transactions and filter in Python
    for txn in self.transactions.all():
        meta_type = txn.meta.get('type', '')
        
        if txn.type == Transaction.CREDIT:
            if meta_type in ['passive', 'referral', 'milestone', 'global_pool', 'referral_correction']:
                if txn.meta.get('source') != 'signup-initial' and not txn.meta.get('non_income', False):
                    credits += txn.amount_usd
        
        elif txn.type == Transaction.DEBIT:
            if meta_type in ['withdrawal', 'referral_reversal']:
                debits += txn.amount_usd
    
    return (credits - debits).quantize(Decimal('0.01'))
```

## Testing

After applying the fix, test with:

```powershell
$env:DATABASE_URL = "YOUR_PRODUCTION_DATABASE_URL_HERE"
python "c:\Users\Ayesha Jahangir\Downloads\nexocart-redline-dash\ref_backend\test_income_calc.py"
```

Expected output:
- Stored income_usd: $1.76
- Calculated income: $1.76
- Match: ✅ YES

## Deployment

1. Test locally against production database
2. Commit changes to git
3. Push to Render
4. Verify in admin panel that income shows correctly