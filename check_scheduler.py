#!/usr/bin/env python
"""
Quick Scheduler Status Checker
===============================

This script checks if the passive earnings scheduler is running.
Run this locally or in Render shell.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.earnings.scheduler import scheduler
from django.conf import settings

print("\n" + "="*70)
print("🔍 SCHEDULER STATUS CHECK")
print("="*70 + "\n")

# Check settings
print("📋 Configuration:")
print(f"  - ENABLE_SCHEDULER: {getattr(settings, 'ENABLE_SCHEDULER', 'Not set')}")
print(f"  - DEBUG: {settings.DEBUG}")
print(f"  - Environment: {'Development' if settings.DEBUG else 'Production'}")

# Check scheduler
print(f"\n⚙️  Scheduler Status:")
print(f"  - Running: {scheduler.running}")
print(f"  - State: {scheduler.state}")

if scheduler.running:
    jobs = scheduler.get_jobs()
    print(f"  - Jobs Count: {len(jobs)}")
    
    if jobs:
        print(f"\n📅 Scheduled Jobs:")
        for job in jobs:
            print(f"  - {job.id}")
            print(f"    Next run: {job.next_run_time}")
            print(f"    Trigger: {job.trigger}")
    
    print("\n✅ Scheduler is RUNNING - Passive earnings will be automated!")
else:
    print("\n❌ Scheduler is NOT running")
    print("\nPossible reasons:")
    print("  1. ENABLE_SCHEDULER is set to False")
    print("  2. Running in DEBUG mode (development)")
    print("  3. Scheduler failed to start (check logs)")
    print("  4. Running a management command (scheduler disabled)")

print("\n" + "="*70 + "\n")