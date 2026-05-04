#!/usr/bin/env python3
"""
Test script to verify account persistence
"""

import sqlite3
import os

# Check if data directory exists
if os.path.exists("data"):
    print("✓ Data directory exists")
    
    # Check each server database
    for i in range(1, 4):
        db_path = f"data/server_{i}.db"
        if os.path.exists(db_path):
            print(f"\n✓ Server {i} database exists: {db_path}")
            
            # Connect and check accounts
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT phone, balance FROM accounts")
            accounts = cursor.fetchall()
            
            if accounts:
                print(f"  Accounts in Server {i}:")
                for phone, balance in accounts:
                    print(f"    - {phone}: UGX {balance:,.2f}")
            else:
                print(f"  No accounts in Server {i}")
            
            conn.close()
        else:
            print(f"✗ Server {i} database not found")
else:
    print("✗ Data directory does not exist")
    print("  Run servers first to create databases")
