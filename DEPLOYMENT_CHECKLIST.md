# Deployment Checklist

## ✅ Pre-Deployment

- [ ] Review all code changes
- [ ] Read `COMPLETE_FIX_SUMMARY.md`
- [ ] Read `QUICK_START_GUIDE.md`
- [ ] Understand the fix (see `VISUAL_SUMMARY.md`)

---

## 🚀 Deployment Steps

### Step 1: Commit Changes
```bash
git status  # Check what files changed
git add .
git commit -m "Fix: Duplicate bonuses and actual deposit amount calculation"
```

**Expected files changed:**
- ✅ `apps/accounts/signals.py`
- ✅ `apps/referrals/services.py`
- ✅ `apps/referrals/models.py`
- ✅ `apps/referrals/migrations/0003_*.py`
- ✅ Multiple new `.py` scripts
- ✅ Multiple new `.md` documentation files

**Checklist:**
- [ ] All expected files are staged
- [ ] No unexpected files are staged
- [ ] Commit message is clear

---

### Step 2: Push to GitHub
```bash
git push origin main
```

**Checklist:**
- [ ] Push successful
- [ ] No errors in terminal
- [ ] Changes visible on GitHub

---

### Step 3: Monitor Render Deployment

1. Go to https://dashboard.render.com
2. Click on your backend service
3. Watch the deployment logs

**Checklist:**
- [ ] Deployment started automatically
- [ ] No errors in build logs
- [ ] Migration applied successfully
- [ ] Deployment status: "Live"
- [ ] No error messages in logs

**Common log messages to look for:**
```
✅ "Running migrations..."
✅ "Applying referrals.0003_..."
✅ "Migrations complete"
✅ "Starting server..."
```

---

### Step 4: Verify Deployment

In Render Shell, run:
```bash
python manage.py showmigrations referrals
```

**Expected output:**
```
referrals
 [X] 0001_initial
 [X] 0002_...
 [X] 0003_referralmilestoneprogress_current_sum_usd_and_more
```

**Checklist:**
- [ ] All migrations show `[X]` (applied)
- [ ] Migration 0003 is applied
- [ ] No errors

---

### Step 5: Clean Up Existing Duplicates

In Render Shell, run:
```bash
python cleanup_duplicate_bonuses.py
```

**Follow the prompts:**
1. Enter user email (or press Enter for default)
2. Review the duplicates found
3. Confirm cleanup (type 'yes')

**Checklist:**
- [ ] Script ran without errors
- [ ] Duplicates identified
- [ ] Duplicates removed
- [ ] Transactions reversed
- [ ] Wallet balances updated

---

### Step 6: Verify the Fix

In Render Shell, run:
```bash
python verify_actual_deposit_fix.py
```

**Expected output:**
```
✅ Correct bonuses: X
⚠️  Issues found: 0

🎉 All bonuses are calculated correctly!
```

**Checklist:**
- [ ] Script ran without errors
- [ ] No issues found for NEW approvals
- [ ] Old approvals may show old behavior (expected)

---

## 🧪 Testing

### Test 1: Create Test User with 1410 PKR

1. **Create user** in admin panel
2. **Add SignupProof** with 1410 PKR
3. **Approve user**
4. **Check referrer's wallet**

**Expected:**
- [ ] L1 bonus: Rs84
- [ ] L2 bonus: Rs42 (if L2 exists)
- [ ] L3 bonus: Rs14 (if L3 exists)
- [ ] No duplicate bonuses

---

### Test 2: Create Test User with 5410 PKR

1. **Create user** in admin panel
2. **Add SignupProof** with 5410 PKR
3. **Approve user**
4. **Check referrer's wallet**

**Expected:**
- [ ] L1 bonus: Rs325 (NOT Rs84!)
- [ ] L2 bonus: Rs162 (if L2 exists)
- [ ] L3 bonus: Rs54 (if L3 exists)
- [ ] No duplicate bonuses

---

### Test 3: Multiple Saves (Duplicate Prevention)

1. **Approve a user**
2. **Edit user** (change name, etc.)
3. **Save user** multiple times
4. **Check referrer's wallet**

**Expected:**
- [ ] Only 1 bonus created
- [ ] No duplicates even after multiple saves
- [ ] Wallet balance correct

---

## 📊 Verification Commands

Run these in Render Shell to verify everything:

### Check specific user:
```bash
python check_user_deposits.py
# Enter your email when prompted
```

### Calculate expected bonuses:
```bash
python calculate_expected_bonuses.py
# Try different amounts: 1410, 5410, 10000
```

### Diagnose duplicates:
```bash
python diagnose_duplicate_bonuses.py
# Enter user email to check for duplicates
```

---

## ✅ Post-Deployment Checklist

### Immediate (Within 1 hour):
- [ ] Deployment successful
- [ ] Migration applied
- [ ] Cleanup script executed
- [ ] Test user 1 (1410 PKR) approved successfully
- [ ] Test user 2 (5410 PKR) approved successfully
- [ ] Bonuses calculated correctly
- [ ] No duplicates created

### Short-term (Within 24 hours):
- [ ] Monitor Render logs for errors
- [ ] Check a few real user approvals
- [ ] Verify bonuses are correct
- [ ] No duplicate bonus reports
- [ ] Run verification script again

### Long-term (Within 1 week):
- [ ] All new approvals working correctly
- [ ] No duplicate bonus issues
- [ ] Variable deposit amounts working
- [ ] Users receiving correct bonuses
- [ ] No complaints about wrong amounts

---

## 🆘 Troubleshooting

### Issue: Deployment Failed

**Check:**
- [ ] GitHub push successful?
- [ ] Render connected to correct repo?
- [ ] Check Render build logs for errors

**Solution:**
- Fix errors in code
- Commit and push again
- Or rollback: `git revert HEAD && git push`

---

### Issue: Migration Not Applied

**Check:**
```bash
python manage.py showmigrations referrals
```

**Solution:**
```bash
python manage.py migrate referrals
```

---

### Issue: Bonuses Still Wrong

**Check:**
- [ ] Was user approved AFTER deployment?
- [ ] Does user have SignupProof record?
- [ ] Is amount_pkr field populated?

**Debug:**
```bash
python check_user_deposits.py
# Check the specific user
```

---

### Issue: Duplicates Still Appearing

**Check:**
- [ ] Is migration applied?
- [ ] Did cleanup script run?

**Solution:**
```bash
python manage.py migrate referrals
python cleanup_duplicate_bonuses.py
```

---

### Issue: Script Errors

**Check:**
- [ ] Are you in Render Shell (not local)?
- [ ] Is database connected?
- [ ] Check Render logs

**Solution:**
- Restart Render service
- Check database connection
- Verify environment variables

---

## 🔄 Rollback Procedure

If critical issues occur:

### Option 1: Git Revert
```bash
git revert HEAD
git push origin main
# Wait for Render to redeploy
```

### Option 2: Render Manual Deploy
1. Go to Render dashboard
2. Click your service
3. Click "Manual Deploy"
4. Select previous deployment

**After rollback:**
- [ ] Verify old version is running
- [ ] Check that system is stable
- [ ] Identify what went wrong
- [ ] Fix issues before redeploying

---

## 📞 Support Resources

### Documentation:
- `COMPLETE_FIX_SUMMARY.md` - Full technical details
- `QUICK_START_GUIDE.md` - Quick reference
- `VISUAL_SUMMARY.md` - Visual explanation
- `ACTUAL_DEPOSIT_BONUS_FIX.md` - Deposit amount fix details
- `DUPLICATE_BONUS_FIX_README.md` - Duplicate fix details

### Scripts:
- `check_user_deposits.py` - Check user bonuses
- `verify_actual_deposit_fix.py` - Verify fix working
- `calculate_expected_bonuses.py` - Calculate expected amounts
- `diagnose_duplicate_bonuses.py` - Find duplicates
- `cleanup_duplicate_bonuses.py` - Remove duplicates

### Logs:
- Render Dashboard → Your Service → Logs
- Look for errors, warnings, migration messages

---

## ✅ Final Verification

Before marking as complete, verify:

- [ ] ✅ Code deployed to production
- [ ] ✅ Migration applied successfully
- [ ] ✅ Cleanup script executed
- [ ] ✅ Test users approved successfully
- [ ] ✅ Bonuses calculated correctly (1410→Rs84, 5410→Rs325)
- [ ] ✅ No duplicate bonuses created
- [ ] ✅ Verification script shows all green
- [ ] ✅ No errors in Render logs
- [ ] ✅ System stable and working

**All checked? Congratulations! 🎉 The fix is complete!**

---

## 📅 Next Steps

1. **Monitor** for 24-48 hours
2. **Check** new user approvals
3. **Verify** bonuses are correct
4. **Document** any issues
5. **Celebrate** the fix! 🎊

---

**Deployment Date:** _________________

**Deployed By:** _________________

**Status:** ⬜ Pending | ⬜ In Progress | ⬜ Complete | ⬜ Rolled Back

**Notes:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________