# Quick Start Guide - Referral Bonus Fix

## 🚀 Deploy in 3 Steps

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Fix: Duplicate bonuses and actual deposit amount calculation"
git push origin main
```

### Step 2: Wait for Render Auto-Deploy
- Go to https://dashboard.render.com
- Wait for deployment to complete (usually 2-5 minutes)
- Check logs for any errors

### Step 3: Clean Up Duplicates (In Render Shell)
```bash
python cleanup_duplicate_bonuses.py
```

**Done! ✅**

---

## 🧪 Quick Test

After deployment, test with a new user:

1. **Create a test user** with 5410 PKR signup proof
2. **Approve the user** in admin panel
3. **Check referrer's wallet** - should see Rs325 bonus (not Rs84)

---

## 📊 Expected Bonuses

| Deposit | L1 Bonus (6%) | L2 Bonus (3%) | L3 Bonus (1%) |
|---------|---------------|---------------|---------------|
| 1410 PKR | Rs84 | Rs42 | Rs14 |
| 5410 PKR | Rs325 | Rs162 | Rs54 |
| 10000 PKR | Rs600 | Rs300 | Rs100 |

*(Exchange rate: 280 PKR/USD)*

---

## 🛠️ Useful Commands (Render Shell)

### Check if fix is working:
```bash
python verify_actual_deposit_fix.py
```

### Calculate expected bonuses:
```bash
python calculate_expected_bonuses.py
```

### Check user's bonuses:
```bash
python check_user_deposits.py
```

### Find duplicates:
```bash
python diagnose_duplicate_bonuses.py
```

### Remove duplicates:
```bash
python cleanup_duplicate_bonuses.py
```

---

## ❓ FAQ

### Q: Will this fix existing wrong bonuses?
**A:** No, only new approvals after deployment. Use `cleanup_duplicate_bonuses.py` to remove duplicates.

### Q: What if a user has no SignupProof?
**A:** System falls back to default 1410 PKR (from settings).

### Q: How do I access Render Shell?
**A:** 
1. Go to Render dashboard
2. Click your backend service
3. Click "Shell" tab
4. Run commands

### Q: How do I know if it's working?
**A:** Run `python verify_actual_deposit_fix.py` in Render Shell.

---

## 🆘 Troubleshooting

### Issue: Bonuses still wrong
- **Check:** Is the deployment complete?
- **Check:** Did you approve the user AFTER deployment?
- **Check:** Does the user have a SignupProof record?

### Issue: Duplicates still appearing
- **Solution:** Run `python cleanup_duplicate_bonuses.py`
- **Check:** Migration applied? Run `python manage.py migrate`

### Issue: Script errors
- **Check:** Are you in Render Shell (not local terminal)?
- **Check:** Is the database connected? Check Render logs

---

## 📞 Need Help?

1. Check `COMPLETE_FIX_SUMMARY.md` for detailed info
2. Check Render logs for errors
3. Run diagnostic scripts to identify issues

---

## ✅ Success Checklist

- [ ] Code pushed to GitHub
- [ ] Render deployment completed
- [ ] Migration applied (auto or manual)
- [ ] Cleanup script executed
- [ ] Test user approved with 5410 PKR
- [ ] Referrer received Rs325 bonus (not Rs84)
- [ ] No duplicate bonuses created
- [ ] Verification script shows all green ✅

**All done? Congratulations! 🎉**