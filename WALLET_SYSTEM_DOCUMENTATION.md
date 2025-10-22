# Wallet System Documentation

## Overview
This document explains how the wallet system works, including balance types, income tracking, and automated earnings generation.

---

## Wallet Balance Types

### 1. **Available Balance** (`available_usd`)
- **Purpose**: Shows the 80% user share of deposits ONLY
- **Source**: Deposits credited by admin
- **Formula**: `Sum of (deposit_amount * 0.80)`
- **Example**: User deposits 1006.25 PKR (805 USD) → Available Balance = 805 USD
- **Display**: User Dashboard "Available Balance" card
- **Note**: This does NOT include passive earnings, referrals, milestones, or global pool

### 2. **Current Income** (`current_income_usd`)
- **Purpose**: Shows total earnings from all income sources
- **Sources**: 
  - Passive earnings (daily 0.4% - 1.3%)
  - Referral bonuses (6% L1, 3% L2, 1% L3)
  - Milestone rewards (when referral targets are met)
  - Global pool distributions (weekly)
- **Formula**: `(Passive + Referral + Milestone + Global Pool) - Withdrawals`
- **Calculation**: Computed from Transaction records with `meta.type` filtering
- **Display**: 
  - User Dashboard "Current Income" card
  - Admin UI "Current Income" column (NOT "Available Balance")

### 3. **Passive Earnings** (`passive_earnings_usd`)
- **Purpose**: Shows only passive income (subset of Current Income)
- **Source**: Daily passive earnings based on investment days
- **Schedule**:
  - Days 1-10: 0.4% daily
  - Days 11-20: 0.6% daily
  - Days 21-30: 0.8% daily
  - Days 31-60: 1.0% daily
  - Days 61-90: 1.3% daily
- **Display**: User Dashboard "Passive Income" card

### 4. **Hold Balance** (`hold_usd`)
- **Purpose**: Platform's 20% hold from deposits and passive earnings
- **Source**: 
  - 20% of deposits
  - Platform share of passive earnings
- **Display**: Not shown to users (internal tracking)

### 5. **Stored Income** (`income_usd`)
- **Purpose**: Cached/stored value of withdrawable income
- **Source**: Updated when passive/referral/milestone/global pool earnings are credited
- **Note**: `current_income_usd` (calculated) is the source of truth, not this field

---

## Transaction Types

All income and balance changes are tracked via `Transaction` records with metadata:

### Income Transactions (CREDIT)
```python
# Passive Earnings
{
  "type": "passive",
  "day_index": 15,
  "percent": "0.006"
}

# Referral Bonuses
{
  "type": "referral",
  "trigger": "join",
  "level": 1,
  "from_user_id": 123
}

# Milestone Rewards
{
  "type": "milestone",
  "target": 10,
  "percent": "0.05"
}

# Global Pool Distribution
{
  "type": "global_pool",
  "week": "2024-W42",
  "share_percent": "0.025"
}

# Deposits (NOT income)
{
  "type": "deposit",
  "id": 456,
  "tx_id": "TXN123",
  "user_share_usd": "805.00",
  "platform_hold_usd": "201.25",
  "global_pool_usd": "100.62"
}
```

### Withdrawal Transactions (DEBIT)
```python
{
  "type": "withdrawal",
  "request_id": 789,
  "method": "BANK",
  "account_name": "John Doe"
}
```

---

## Automated Earnings System

### Daily Passive Earnings
Passive earnings are generated automatically every day at **00:01 UTC**.

#### How It Works:
1. **Scheduler**: APScheduler runs in background (configured in `settings.py`)
2. **Command**: Calls `run_daily_earnings` management command
3. **Process**:
   - Finds all approved users with credited deposits
   - Calculates days since first deposit
   - Generates earnings for the next day (day_index + 1)
   - Stops at day 90 (max earning period)
   - Updates `wallet.income_usd` (NOT `available_usd`)
   - Creates Transaction record with `meta.type='passive'`

#### Enable/Disable:
```bash
# Enable scheduler (production)
export ENABLE_SCHEDULER=true

# Disable scheduler (development)
export ENABLE_SCHEDULER=false
```

#### Configuration:
```python
# settings.py
SCHEDULER_CONFIG = {
    'DAILY_EARNINGS_HOUR': 0,      # 00:00 UTC
    'DAILY_EARNINGS_MINUTE': 1,    # 00:01 UTC
    'HEARTBEAT_INTERVAL': 3600,    # 1 hour
}
```

### Weekly Global Pool Distribution
Global pool earnings are distributed every **Monday at 00:00 UTC** via cron.

```python
# settings.py
CRONJOBS = [
    ('0 0 * * 1', 'django.core.management.call_command', ['distribute_global_pool']),
]
```

---

## Backfill Commands

### 1. Backfill from Start (Recommended)
Generates all missing passive earnings from first deposit date until today.

```bash
# Dry run (preview only)
python manage.py backfill_from_start --dry-run

# Execute backfill
python manage.py backfill_from_start

# Backfill specific user
python manage.py backfill_from_start --user-id 123
```

**What it does:**
- Finds first credited deposit date (excluding SIGNUP-INIT)
- Calculates days since first deposit
- Generates earnings for all missing days (up to day 90)
- Updates `wallet.income_usd` (NOT `available_usd`)
- Creates Transaction records for each day

### 2. Backfill Specific Days
Backfills a specific number of days (legacy command).

```bash
# Backfill last 7 days
python manage.py backfill_daily_earnings --days 7

# Backfill last 30 days
python manage.py backfill_daily_earnings --days 30

# Dry run
python manage.py backfill_daily_earnings --days 90 --dry-run
```

### 3. Run Daily Earnings Manually
Manually trigger today's earnings generation.

```bash
# Generate today's earnings
python manage.py run_daily_earnings

# Backfill from specific date
python manage.py run_daily_earnings --backfill-from-date 2024-01-01

# Dry run
python manage.py run_daily_earnings --dry-run
```

---

## API Endpoints

### User Dashboard API

#### Get Wallet
```http
GET /api/wallets/me/
Authorization: Bearer <token>

Response:
{
  "available_usd": 805.00,           // 80% of deposits only
  "hold_usd": 201.25,                // Platform hold
  "income_usd": 45.50,               // Stored income (cached)
  "current_income_usd": 45.50,       // Calculated income (source of truth)
  "passive_earnings_usd": 32.40      // Passive earnings only
}
```

#### Get Transactions
```http
GET /api/wallets/me/transactions/
Authorization: Bearer <token>

Response: [
  {
    "id": 123,
    "type": "CREDIT",
    "amount_usd": 3.22,
    "meta": {
      "type": "passive",
      "day_index": 15,
      "percent": "0.006"
    },
    "created_at": "2024-01-15T00:01:00Z"
  },
  ...
]
```

### Admin UI API

#### Get Users List
```http
GET /api/admin/users/
Authorization: Bearer <admin_token>

Response:
{
  "results": [
    {
      "id": 123,
      "username": "john_doe",
      "current_balance_usd": "805.00",      // Available balance (deposits)
      "current_income_usd": "45.50",        // Total income (USE THIS)
      "passive_income_usd": "32.40",        // Passive earnings only
      ...
    }
  ]
}
```

**Important**: Admin UI should display `current_income_usd`, NOT `current_balance_usd`.

---

## Frontend Display

### User Dashboard (`DashboardOverview.tsx`)

```typescript
// Three separate cards:

1. Current Income Card
   - Value: wallet.current_income_usd
   - Description: "Total earnings from all sources"
   - Includes: Passive + Referral + Milestone + Global Pool

2. Passive Income Card
   - Value: wallet.passive_earnings_usd
   - Description: "Days 1–10: 0.4% • 11–20: 0.6% • ..."
   - Includes: Only passive earnings

3. Available Balance Card
   - Value: wallet.available_usd
   - Description: "Ready for withdrawal"
   - Includes: 80% of deposits ONLY
```

### Admin UI

```javascript
// User list table columns:
- Username
- Email
- Current Income (USD)  ← Use current_income_usd
- Passive Income (USD)  ← Use passive_income_usd
- Available Balance (USD) ← Use current_balance_usd (optional)
```

---

## Database Schema

### Wallet Model
```python
class Wallet(models.Model):
    user = OneToOneField(User)
    available_usd = DecimalField()  # 80% of deposits only
    hold_usd = DecimalField()       # Platform 20% hold
    income_usd = DecimalField()     # Stored income (cached)
    
    def get_current_income_usd(self):
        """Calculate from transactions (source of truth)"""
        # Sum: passive + referral + milestone + global_pool
        # Minus: withdrawals
```

### Transaction Model
```python
class Transaction(models.Model):
    wallet = ForeignKey(Wallet)
    type = CharField()  # CREDIT or DEBIT
    amount_usd = DecimalField()
    meta = JSONField()  # {"type": "passive", "day_index": 15, ...}
    created_at = DateTimeField()
```

### PassiveEarning Model
```python
class PassiveEarning(models.Model):
    user = ForeignKey(User)
    day_index = IntegerField()  # 1-90
    percent = DecimalField()    # 0.004 - 0.013
    amount_usd = DecimalField()
    created_at = DateTimeField()
```

---

## Common Issues & Solutions

### Issue: Current Income shows 0 even with deposits
**Cause**: No passive earnings have been generated yet.
**Solution**: Run backfill command:
```bash
python manage.py backfill_from_start
```

### Issue: Available Balance includes passive earnings
**Cause**: Old backfill command was adding to `available_usd`.
**Solution**: 
1. Fixed in new `backfill_from_start.py` command
2. Passive earnings now go to `income_usd` only
3. Run `backfill_from_start` to regenerate correctly

### Issue: Passive earnings not generating daily
**Cause**: Scheduler is disabled.
**Solution**: Enable scheduler:
```bash
export ENABLE_SCHEDULER=true
python manage.py runserver
```

### Issue: Admin UI shows "Available Balance" instead of "Current Income"
**Cause**: Frontend is using wrong field.
**Solution**: Update admin UI to use `current_income_usd` field.

---

## Testing

### Test Passive Earnings Generation
```bash
# 1. Check current status
python manage.py check_passive_earnings_status

# 2. Run dry-run backfill
python manage.py backfill_from_start --dry-run

# 3. Execute backfill
python manage.py backfill_from_start

# 4. Verify in database
python manage.py shell
>>> from apps.wallets.models import Wallet
>>> w = Wallet.objects.get(user__username='john_doe')
>>> print(f"Available: ${w.available_usd}")
>>> print(f"Income: ${w.income_usd}")
>>> print(f"Current Income: ${w.get_current_income_usd()}")
```

### Test Scheduler
```bash
# Enable debug mode (generates earnings every 5 minutes)
export ENABLE_DEBUG_SCHEDULER=true
export ENABLE_SCHEDULER=true
python manage.py runserver

# Check logs for:
# "✅ Automated earnings scheduler started successfully"
# "💓 Scheduler heartbeat - automation system is running"
```

---

## Summary

| Field | Purpose | Source | Display Location |
|-------|---------|--------|------------------|
| `available_usd` | 80% of deposits | Deposit credits | User Dashboard "Available Balance" |
| `current_income_usd` | Total earnings | Calculated from transactions | User Dashboard "Current Income", Admin UI |
| `passive_earnings_usd` | Passive earnings only | Calculated from passive transactions | User Dashboard "Passive Income" |
| `income_usd` | Cached income | Updated on earnings credit | Internal (not primary display) |
| `hold_usd` | Platform hold | 20% of deposits + platform share | Internal only |

**Key Rule**: 
- **Available Balance** = Deposits ONLY (805 USD)
- **Current Income** = Passive + Referral + Milestone + Global Pool
- **Passive Earnings** = Subset of Current Income (passive only)

---

## Next Steps

1. ✅ Run backfill to generate historical earnings:
   ```bash
   python manage.py backfill_from_start
   ```

2. ✅ Enable scheduler for daily automation:
   ```bash
   export ENABLE_SCHEDULER=true
   ```

3. ✅ Update Admin UI to show "Current Income" instead of "Available Balance"

4. ✅ Test the system:
   - Check user dashboard displays all three values correctly
   - Verify admin UI shows current income
   - Confirm scheduler is running (check logs)

---

**Last Updated**: 2024-01-08
**Version**: 2.0