#!/usr/bin/env python
"""
Calculate Expected Bonuses
===========================

This script calculates what referral bonuses SHOULD be for different deposit amounts.
Use this to verify your understanding of the bonus calculation.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from decimal import Decimal

print("\n" + "="*80)
print("💰 REFERRAL BONUS CALCULATOR")
print("="*80 + "\n")

rate = Decimal(str(settings.ADMIN_USD_TO_PKR))
print(f"Exchange Rate: {rate} PKR/USD")
print(f"Referral Rates: L1=6%, L2=3%, L3=1%")
print()

# Common deposit amounts
deposit_amounts = [1410, 5410, 10000, 15000, 20000]

print("="*80)
print(f"{'Deposit (PKR)':<15} {'USD':<10} {'L1 (6%)':<15} {'L2 (3%)':<15} {'L3 (1%)':<15}")
print("="*80)

for amount_pkr in deposit_amounts:
    amount_pkr_dec = Decimal(str(amount_pkr))
    amount_usd = (amount_pkr_dec / rate).quantize(Decimal('0.01'))
    
    l1_usd = (amount_usd * Decimal('0.06')).quantize(Decimal('0.01'))
    l2_usd = (amount_usd * Decimal('0.03')).quantize(Decimal('0.01'))
    l3_usd = (amount_usd * Decimal('0.01')).quantize(Decimal('0.01'))
    
    l1_pkr = (l1_usd * rate).quantize(Decimal('0.01'))
    l2_pkr = (l2_usd * rate).quantize(Decimal('0.01'))
    l3_pkr = (l3_usd * rate).quantize(Decimal('0.01'))
    
    print(f"{amount_pkr:<15} ${amount_usd:<9} Rs{l1_pkr:<13} Rs{l2_pkr:<13} Rs{l3_pkr:<13}")

print("="*80)

# Interactive calculator
print("\n" + "="*80)
print("🧮 CUSTOM AMOUNT CALCULATOR")
print("="*80 + "\n")

while True:
    try:
        user_input = input("Enter deposit amount in PKR (or 'q' to quit): ").strip()
        
        if user_input.lower() in ['q', 'quit', 'exit']:
            break
        
        amount_pkr = Decimal(user_input)
        amount_usd = (amount_pkr / rate).quantize(Decimal('0.01'))
        
        print(f"\n💰 Deposit: {amount_pkr} PKR = ${amount_usd} USD")
        print(f"   Exchange Rate: {rate} PKR/USD")
        print()
        
        # L1 Bonus
        l1_usd = (amount_usd * Decimal('0.06')).quantize(Decimal('0.01'))
        l1_pkr = (l1_usd * rate).quantize(Decimal('0.01'))
        print(f"   📊 L1 Bonus (6%):")
        print(f"      ${l1_usd} USD = Rs{l1_pkr} PKR")
        
        # L2 Bonus
        l2_usd = (amount_usd * Decimal('0.03')).quantize(Decimal('0.01'))
        l2_pkr = (l2_usd * rate).quantize(Decimal('0.01'))
        print(f"   📊 L2 Bonus (3%):")
        print(f"      ${l2_usd} USD = Rs{l2_pkr} PKR")
        
        # L3 Bonus
        l3_usd = (amount_usd * Decimal('0.01')).quantize(Decimal('0.01'))
        l3_pkr = (l3_usd * rate).quantize(Decimal('0.01'))
        print(f"   📊 L3 Bonus (1%):")
        print(f"      ${l3_usd} USD = Rs{l3_pkr} PKR")
        
        # Total
        total_usd = l1_usd + l2_usd + l3_usd
        total_pkr = (total_usd * rate).quantize(Decimal('0.01'))
        print(f"\n   💵 Total Bonuses (all levels):")
        print(f"      ${total_usd} USD = Rs{total_pkr} PKR")
        print()
        
    except ValueError:
        print("❌ Invalid amount. Please enter a number.")
    except KeyboardInterrupt:
        print("\n\nExiting...")
        break
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*80 + "\n")