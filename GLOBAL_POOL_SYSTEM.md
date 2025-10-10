# 🌍 Global Pool System Documentation

## Overview

The Global Pool is a weekly reward system that:
1. **Collects** 0.5% from all Monday signup deposits (SIGNUP-INIT)
2. **Distributes** the collected pool equally among ALL active users on Monday

---

## 📊 How It Works

### Collection Phase (Monday)
```
Monday Signup → Admin Approves → 0.5% goes to Global Pool
```

**Example:**
- User A signs up Monday with 5,410 PKR ($19.32)
- User B signs up Monday with 10,000 PKR ($35.71)
- User C signs up Monday with 15,000 PKR ($53.57)

**Collection:**
- User A: $19.32 × 0.5% = $0.10
- User B: $35.71 × 0.5% = $0.18
- User C: $53.57 × 0.5% = $0.27
- **Total Pool: $0.55**

### Distribution Phase (Monday)
```
Pool Balance → Divide by Active Users → Credit to Each User
```

**Example:**
- Pool: $0.55
- Active Users: 10
- Per User: $0.55 ÷ 10 = $0.055 ≈ $0.06

**Each user receives:**
- Income (80%): $0.05
- Platform Hold (20%): $0.01

---

## 🔄 Weekly Cycle

```
┌─────────────────────────────────────────────────────────────┐
│  MONDAY - Week 1                                            │
├─────────────────────────────────────────────────────────────┤
│  Morning: Collect 0.5% from Monday signups                  │
│  ├─ User A signup: $19.32 → Pool gets $0.10                │
│  ├─ User B signup: $35.71 → Pool gets $0.18                │
│  └─ User C signup: $53.57 → Pool gets $0.27                │
│                                                              │
│  Pool Balance: $0.55                                        │
│                                                              │
│  Evening: Distribute pool to all users                      │
│  ├─ 10 active users                                         │
│  ├─ Each gets: $0.06                                        │
│  └─ Pool reset to: $0.00                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  TUESDAY - SUNDAY (Week 1)                                  │
├─────────────────────────────────────────────────────────────┤
│  No global pool activity                                    │
│  Pool remains at: $0.00                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  MONDAY - Week 2                                            │
├─────────────────────────────────────────────────────────────┤
│  Cycle repeats...                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Protection Against Duplicates

### Three Layers of Protection:

1. **Collection Protection**
   - `unique_together = ("user", "collection_date")`
   - One collection per user per Monday

2. **Distribution Protection**
   - `unique_together = ("user", "distribution_date")`
   - One distribution per user per Monday

3. **State Tracking**
   - `last_collection_date` - Tracks last Monday collected
   - `last_distribution_date` - Tracks last Monday distributed
   - Prevents re-processing the same Monday

---

## 📁 Database Models

### GlobalPoolState (Singleton)
```python
current_pool_usd              # Current pool balance
last_collection_date          # Last Monday collected
last_distribution_date        # Last Monday distributed
total_collected_all_time      # Lifetime collection stats
total_distributed_all_time    # Lifetime distribution stats
```

### GlobalPoolCollection
```python
user                          # User who signed up
signup_amount_usd             # Their signup amount
collection_amount_usd         # 0.5% collected
collection_date               # Monday date
```

### GlobalPoolDistribution
```python
user                          # User who received
amount_usd                    # Amount received
distribution_date             # Monday date
total_pool_amount             # Total pool distributed
total_users                   # Number of users
```

---

## 🚀 Automation

### Middleware (Automatic)
The system runs automatically via middleware on Mondays:

```python
# In AutoDailyEarningsMiddleware
if today.weekday() == 0:  # Monday
    _process_global_pool_monday(today)
```

**Process:**
1. First request on Monday triggers the middleware
2. Middleware checks if today is Monday
3. If yes, runs collection and distribution
4. All subsequent requests skip (already processed)

### Manual Command (Optional)
You can also run manually:

```bash
# Collect only
python manage.py process_global_pool --collect

# Distribute only
python manage.py process_global_pool --distribute

# Both
python manage.py process_global_pool --both

# Specific Monday
python manage.py process_global_pool --both --date 2025-01-13
```

---

## 💰 Transaction Records

### Collection (No Transaction)
- Collection is tracked in `GlobalPoolCollection` model
- No wallet transaction created (just tracking)

### Distribution (Creates Transaction)
```json
{
  "type": "CREDIT",
  "amount_usd": 0.06,
  "meta": {
    "type": "global_pool",
    "distribution_date": "2025-01-13",
    "total_pool": "0.55",
    "total_users": 10,
    "user_share": "0.05",
    "platform_hold": "0.01"
  }
}
```

---

## 📊 Frontend Display

### Current Implementation
The frontend already supports global pool display:

```typescript
// In DashboardOverview.tsx
const currentIncomeUsd = useMemo(() => {
  // Includes global_pool transactions
  if (metaType === 'global_pool') return true;
}, [wallet, txns]);
```

### Transaction Label
```typescript
if (metaType === 'global_pool') return 'Global Pool Reward';
```

---

## 🔍 Admin Panel

### View Global Pool State
- Navigate to: **Admin → Earnings → Global Pool States**
- See: Current pool, last collection/distribution dates, lifetime stats

### View Collections
- Navigate to: **Admin → Earnings → Global Pool Collections**
- Filter by: Collection date
- See: Who signed up, how much collected

### View Distributions
- Navigate to: **Admin → Earnings → Global Pool Distributions**
- Filter by: Distribution date
- See: Who received, how much distributed

---

## 📈 Example Scenario

### Scenario: First Monday After Database Reset

**Initial State:**
- Pool: $0.00
- Last Collection: None
- Last Distribution: None

**Monday Morning (10:00 AM):**
- User visits website → Middleware triggers
- Checks: Is today Monday? ✅ Yes
- Checks: Already collected today? ❌ No
- **Collection Phase:**
  - Finds 3 Monday signups
  - Collects: $0.10 + $0.18 + $0.27 = $0.55
  - Pool now: $0.55

**Monday Evening (Same Day):**
- Another user visits website → Middleware triggers
- Checks: Is today Monday? ✅ Yes
- Checks: Already collected today? ✅ Yes (skip collection)
- Checks: Already distributed today? ❌ No
- **Distribution Phase:**
  - Finds 10 active users
  - Distributes: $0.55 ÷ 10 = $0.06 each
  - Pool now: $0.00

**Result:**
- ✅ 3 users contributed to pool
- ✅ 10 users received from pool
- ✅ Pool reset to $0.00
- ✅ Ready for next Monday

---

## ⚠️ Important Notes

### 1. Only SIGNUP-INIT Deposits
- Regular deposits are NOT included
- Only the initial signup deposit (tx_id='SIGNUP-INIT')

### 2. Only Monday Signups
- Only users who sign up on Monday contribute
- Tuesday-Sunday signups don't contribute

### 3. All Active Users Receive
- No eligibility criteria
- Any user with a wallet receives a share
- Equal distribution (not proportional)

### 4. 80/20 Split Maintained
- User receives 80% in `income_usd` (withdrawable)
- Platform holds 20% in `hold_usd`

### 5. Automatic Processing
- No manual intervention needed
- Runs automatically on first Monday request
- Protected against duplicate processing

---

## 🧪 Testing

### Test Collection
```bash
# Create test users on Monday
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> from apps.wallets.models import DepositRequest
>>> from datetime import datetime
>>> User = get_user_model()
>>> user = User.objects.create_user(username='testuser', password='test123')
>>> DepositRequest.objects.create(
...     user=user,
...     amount_pkr=5410,
...     amount_usd=19.32,
...     fx_rate=280,
...     tx_id='SIGNUP-INIT',
...     status='CREDITED',
...     created_at=datetime.now()
... )

# Run collection
python manage.py process_global_pool --collect
```

### Test Distribution
```bash
# Run distribution
python manage.py process_global_pool --distribute

# Check results
python manage.py shell
>>> from apps.earnings.models import GlobalPoolState
>>> state = GlobalPoolState.objects.get(pk=1)
>>> print(f"Pool: ${state.current_pool_usd}")
>>> print(f"Collected: ${state.total_collected_all_time}")
>>> print(f"Distributed: ${state.total_distributed_all_time}")
```

---

## 📝 Summary

✅ **Automatic**: Runs via middleware on Mondays  
✅ **Protected**: Unique constraints prevent duplicates  
✅ **Tracked**: Full audit trail in database  
✅ **Fair**: Equal distribution to all users  
✅ **Transparent**: Visible in admin panel and frontend  

**Current Status:** ✅ Fully implemented and ready to use!

---

## 🚀 Deployment Checklist

- [x] Models created and migrated
- [x] Admin panel configured
- [x] Middleware updated
- [x] Management command created
- [x] Frontend already supports display
- [x] Protection against duplicates
- [x] Documentation complete

**Next Steps:**
1. Deploy to production
2. Wait for next Monday
3. System will automatically collect and distribute
4. Monitor admin panel for results