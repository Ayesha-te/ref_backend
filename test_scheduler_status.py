"""
Test script to check if the scheduler is working with the base backend URL
"""
import requests
import json

# Backend URL from admin UI
BACKEND_URL = "https://ref-backend-fw8y.onrender.com/api"

# Admin credentials (from app.js quickLogin function)
ADMIN_USERNAME = "Ahmad"
ADMIN_PASSWORD = "12345"

def test_scheduler_status():
    """Test the scheduler status endpoint"""
    print("=" * 60)
    print("SCHEDULER STATUS TEST")
    print("=" * 60)
    print(f"\n🌐 Backend URL: {BACKEND_URL}")
    
    # Step 1: Login to get JWT token
    print("\n📝 Step 1: Logging in as admin...")
    try:
        login_response = requests.post(
            f"{BACKEND_URL}/auth/token/",
            json={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            },
            timeout=10
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed with status {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
        
        tokens = login_response.json()
        access_token = tokens.get('access')
        print(f"✅ Login successful! Got access token: {access_token[:30]}...")
        
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return
    
    # Step 2: Check scheduler status
    print("\n📊 Step 2: Checking scheduler status...")
    try:
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        scheduler_response = requests.get(
            f"{BACKEND_URL}/earnings/scheduler-status/",
            headers=headers,
            timeout=10
        )
        
        if scheduler_response.status_code != 200:
            print(f"❌ Scheduler status check failed with status {scheduler_response.status_code}")
            print(f"Response: {scheduler_response.text}")
            return
        
        status = scheduler_response.json()
        print("\n" + "=" * 60)
        print("SCHEDULER STATUS RESULTS")
        print("=" * 60)
        print(json.dumps(status, indent=2))
        
        # Analyze the results
        print("\n" + "=" * 60)
        print("ANALYSIS")
        print("=" * 60)
        
        enabled = status.get('enabled', False)
        running = status.get('running', False)
        jobs_count = status.get('jobs_count', 0)
        jobs = status.get('jobs', [])
        config = status.get('config', {})
        
        print(f"\n✅ Scheduler Enabled: {enabled}")
        print(f"✅ Scheduler Running: {running}")
        print(f"✅ Jobs Count: {jobs_count}")
        
        if config:
            print(f"\n📋 Configuration:")
            print(f"   - Daily Earnings Hour: {config.get('DAILY_EARNINGS_HOUR', 'N/A')} (UTC)")
            print(f"   - Daily Earnings Minute: {config.get('DAILY_EARNINGS_MINUTE', 'N/A')}")
            print(f"   - Heartbeat Interval: {config.get('HEARTBEAT_INTERVAL', 'N/A')} seconds")
        
        if jobs:
            print(f"\n📅 Scheduled Jobs:")
            for job in jobs:
                print(f"   - {job.get('name', 'Unknown')}")
                print(f"     ID: {job.get('id', 'N/A')}")
                print(f"     Next Run: {job.get('next_run', 'N/A')}")
        
        # Final verdict
        print("\n" + "=" * 60)
        print("VERDICT")
        print("=" * 60)
        
        if enabled and running and jobs_count > 0:
            print("✅ SCHEDULER IS WORKING!")
            print("   The passive income automation is running successfully.")
            print("   Daily earnings will be generated automatically.")
        elif enabled and not running:
            print("⚠️  SCHEDULER IS ENABLED BUT NOT RUNNING!")
            print("   The scheduler is configured but not active.")
            print("   This might be due to server restart or configuration issue.")
        elif not enabled:
            print("❌ SCHEDULER IS DISABLED!")
            print("   Set ENABLE_SCHEDULER=true in environment variables to enable.")
        else:
            print("⚠️  SCHEDULER STATUS UNCLEAR")
            print("   Please check the logs for more information.")
        
    except Exception as e:
        print(f"❌ Scheduler status check error: {str(e)}")
        return

if __name__ == "__main__":
    test_scheduler_status()