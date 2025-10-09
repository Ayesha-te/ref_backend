# PowerShell script to run JSONB query tests against production database
# 
# USAGE:
# 1. Edit this file and paste your DATABASE_URL below
# 2. Run: .\RUN_JSONB_TEST.ps1

# ⚠️ PASTE YOUR PRODUCTION DATABASE_URL HERE:
$DATABASE_URL = "postgresql://neondb_owner:PASTE_YOUR_PASSWORD_HERE@ep-cool-bonus-a5iqvvvv-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

# Set environment variable and run the test
$env:DATABASE_URL = $DATABASE_URL
python "c:\Users\Ayesha Jahangir\Downloads\nexocart-redline-dash\ref_backend\test_jsonb_query.py"