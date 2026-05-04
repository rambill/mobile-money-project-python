#!/usr/bin/env python3
"""
Copy all data from Server 1 to Server 2
Use this after deleting Server 2's database to sync existing accounts
"""

import sqlite3
import os
import sys
import shutil

def copy_database():
    """Copy Server 1 database to Server 2"""
    
    source_db = "data/server_1.db"
    target_db = "data/server_2.db"
    
    print("=" * 60)
    print("COPY DATABASE FROM SERVER 1 TO SERVER 2")
    print("=" * 60)
    
    # Check if source exists
    if not os.path.exists(source_db):
        print(f"\n✗ Source database not found: {source_db}")
        print("  Make sure Server 1 database exists!")
        return False
    
    # Check if target already exists
    if os.path.exists(target_db):
        print(f"\n⚠ Target database already exists: {target_db}")
        response = input("  Do you want to overwrite it? (yes/no): ").strip().lower()
        if response != "yes":
            print("  Cancelled.")
            return False
        print("  Deleting existing database...")
        os.remove(target_db)
    
    # Copy the database file
    print(f"\nCopying {source_db} to {target_db}...")
    try:
        shutil.copy2(source_db, target_db)
        print("✓ Database copied successfully!")
        
        # Verify the copy
        print("\nVerifying copied database...")
        conn = sqlite3.connect(target_db)
        cursor = conn.execute("SELECT COUNT(*) FROM accounts")
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"✓ Found {count} account(s) in copied database")
        
        # Show accounts
        if count > 0:
            conn = sqlite3.connect(target_db)
            cursor = conn.execute("SELECT phone, balance FROM accounts")
            print("\nAccounts in Server 2 database:")
            for row in cursor.fetchall():
                print(f"  - Phone: {row[0]}, Balance: {row[1]}")
            conn.close()
        
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print("\nNow you can start Server 2:")
        print("  python server.py 2")
        print("\nThen test with client.py on Server 2 machine")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error copying database: {e}")
        return False


if __name__ == "__main__":
    print("\n⚠ WARNING: Make sure Server 2 is STOPPED before running this!")
    print("  Press Ctrl+C to cancel, or Enter to continue...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
    
    success = copy_database()
    sys.exit(0 if success else 1)
