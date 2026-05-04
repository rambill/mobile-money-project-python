#!/usr/bin/env python3
"""
Sync data between servers
This script helps resolve data inconsistencies between servers
"""

import sqlite3
import os
import sys

def get_accounts(db_path):
    """Get all accounts from a database"""
    if not os.path.exists(db_path):
        return {}
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT phone, balance, vector_clock FROM accounts")
    
    accounts = {}
    for row in cursor.fetchall():
        accounts[row['phone']] = {
            'balance': row['balance'],
            'vector_clock': row['vector_clock']
        }
    
    conn.close()
    return accounts

def show_differences():
    """Show differences between server databases"""
    print("\n" + "="*60)
    print("  SERVER DATA COMPARISON")
    print("="*60)
    
    # Get accounts from both servers
    server1_accounts = get_accounts("data/server_1.db")
    server2_accounts = get_accounts("data/server_2.db")
    
    if not server1_accounts and not server2_accounts:
        print("\n✗ No data found in either server")
        return
    
    # Find all unique phone numbers
    all_phones = set(server1_accounts.keys()) | set(server2_accounts.keys())
    
    print(f"\nFound {len(all_phones)} unique account(s)")
    print("-"*60)
    
    inconsistencies = []
    
    for phone in sorted(all_phones):
        balance1 = server1_accounts.get(phone, {}).get('balance', 'N/A')
        balance2 = server2_accounts.get(phone, {}).get('balance', 'N/A')
        
        print(f"\nAccount: {phone}")
        print(f"  Server 1: {balance1}")
        print(f"  Server 2: {balance2}")
        
        if balance1 != balance2:
            inconsistencies.append({
                'phone': phone,
                'server1': balance1,
                'server2': balance2
            })
            print(f"  ⚠️  INCONSISTENT!")
        else:
            print(f"  ✓ Consistent")
    
    print("\n" + "="*60)
    
    if inconsistencies:
        print(f"\n⚠️  Found {len(inconsistencies)} inconsistent account(s)")
        print("\nTo fix this:")
        print("1. Stop both servers")
        print("2. Decide which server has the correct data")
        print("3. Delete the database of the incorrect server")
        print("4. Restart both servers")
        print("5. The correct server will replicate to the other")
    else:
        print("\n✓ All accounts are consistent!")

def main():
    if not os.path.exists("data"):
        print("✗ Data directory not found")
        print("  Make sure servers have been run at least once")
        return
    
    show_differences()
    
    print("\n" + "="*60)
    print("  RECOMMENDATION")
    print("="*60)
    print("""
If you see inconsistencies:

Option 1: Use Server 1 as source of truth
  1. Stop both servers
  2. Delete: data/server_2.db
  3. Restart Server 1
  4. Restart Server 2
  5. Server 2 will sync from Server 1

Option 2: Use Server 2 as source of truth
  1. Stop both servers
  2. Delete: data/server_1.db
  3. Restart Server 2
  4. Restart Server 1
  5. Server 1 will sync from Server 2

Option 3: Start fresh
  1. Stop both servers
  2. Delete: data/server_1.db and data/server_2.db
  3. Restart both servers
  4. Register accounts again
""")

if __name__ == "__main__":
    main()
