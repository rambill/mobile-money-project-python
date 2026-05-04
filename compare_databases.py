#!/usr/bin/env python3
"""
Compare databases between Server 1 and Server 2
Shows which accounts are missing or have different balances
"""

import sqlite3
import sys

def get_accounts(db_path):
    """Get all accounts from a database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT phone, balance, pin FROM accounts ORDER BY phone")
        accounts = {}
        for row in cursor.fetchall():
            accounts[row[0]] = {
                "balance": row[1],
                "pin": row[2]
            }
        conn.close()
        return accounts
    except Exception as e:
        print(f"Error reading {db_path}: {e}")
        return {}


def compare_databases():
    """Compare Server 1 and Server 2 databases"""
    
    print("=" * 80)
    print("DATABASE COMPARISON: Server 1 vs Server 2")
    print("=" * 80)
    
    # Get accounts from both servers
    server1_accounts = get_accounts("data/server_1.db")
    server2_accounts = get_accounts("data/server_2.db")
    
    print(f"\nServer 1: {len(server1_accounts)} account(s)")
    print(f"Server 2: {len(server2_accounts)} account(s)")
    
    # Find accounts only on Server 1
    only_server1 = set(server1_accounts.keys()) - set(server2_accounts.keys())
    
    # Find accounts only on Server 2
    only_server2 = set(server2_accounts.keys()) - set(server1_accounts.keys())
    
    # Find accounts with different balances
    different_balances = []
    for phone in set(server1_accounts.keys()) & set(server2_accounts.keys()):
        balance1 = server1_accounts[phone]["balance"]
        balance2 = server2_accounts[phone]["balance"]
        if balance1 != balance2:
            different_balances.append((phone, balance1, balance2))
    
    # Print results
    print("\n" + "=" * 80)
    print("ACCOUNTS ONLY ON SERVER 1 (Missing from Server 2)")
    print("=" * 80)
    
    if only_server1:
        for phone in sorted(only_server1):
            balance = server1_accounts[phone]["balance"]
            print(f"  {phone}: Balance = {balance:,.2f}")
        print(f"\nTotal: {len(only_server1)} account(s) missing from Server 2")
    else:
        print("  ✓ None - Server 2 has all accounts from Server 1")
    
    print("\n" + "=" * 80)
    print("ACCOUNTS ONLY ON SERVER 2 (Missing from Server 1)")
    print("=" * 80)
    
    if only_server2:
        for phone in sorted(only_server2):
            balance = server2_accounts[phone]["balance"]
            print(f"  {phone}: Balance = {balance:,.2f}")
        print(f"\nTotal: {len(only_server2)} account(s) missing from Server 1")
    else:
        print("  ✓ None - Server 1 has all accounts from Server 2")
    
    print("\n" + "=" * 80)
    print("ACCOUNTS WITH DIFFERENT BALANCES")
    print("=" * 80)
    
    if different_balances:
        print(f"\n{'Phone':<15} {'Server 1 Balance':>20} {'Server 2 Balance':>20} {'Difference':>20}")
        print("-" * 80)
        for phone, balance1, balance2 in sorted(different_balances):
            diff = balance1 - balance2
            print(f"{phone:<15} {balance1:>20,.2f} {balance2:>20,.2f} {diff:>20,.2f}")
        print(f"\nTotal: {len(different_balances)} account(s) with different balances")
    else:
        print("  ✓ None - All common accounts have matching balances")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_issues = len(only_server1) + len(only_server2) + len(different_balances)
    
    if total_issues == 0:
        print("\n✓ Databases are in sync!")
        print("  - Same number of accounts")
        print("  - All accounts exist on both servers")
        print("  - All balances match")
    else:
        print(f"\n⚠ Found {total_issues} issue(s):")
        if only_server1:
            print(f"  - {len(only_server1)} account(s) missing from Server 2")
        if only_server2:
            print(f"  - {len(only_server2)} account(s) missing from Server 1")
        if different_balances:
            print(f"  - {len(different_balances)} account(s) with different balances")
        
        print("\n" + "=" * 80)
        print("RECOMMENDED ACTION")
        print("=" * 80)
        print("\nRestart both servers to trigger automatic sync:")
        print("  1. Stop both servers (Ctrl+C)")
        print("  2. Restart Server 1: python server.py 1")
        print("  3. Restart Server 2: python server.py 2")
        print("\nServer 2 will automatically sync differences from Server 1!")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    compare_databases()
