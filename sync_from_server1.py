#!/usr/bin/env python3
"""
Sync data from Server 1 to Server 2
Run this on Server 2 machine after deleting its database
"""

import socket
import json
import sqlite3
import time
import sys

SERVER1_HOST = "10.29.42.224"
SERVER1_PORT = 6001
SERVER2_DB = "data/server_2.db"

def send_request(host, port, command, args):
    """Send a request to a server"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5.0)
        
        # Build request
        req_id = f"sync_{time.time()}"
        message = f"REQ|{req_id}|{command}|" + "|".join(args)
        
        # Send request
        sock.sendto(message.encode(), (host, port))
        
        # Wait for response
        data, _ = sock.recvfrom(2048)
        response = data.decode().strip()
        
        sock.close()
        return response
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def get_account_from_server1(phone, pin):
    """Get account details from Server 1"""
    response = send_request(SERVER1_HOST, SERVER1_PORT, "BALANCE", [phone, pin])
    
    if not response:
        return None
    
    parts = response.split('|')
    if len(parts) >= 5 and parts[2] == "OK":
        balance = float(parts[4])
        vector_clock = parts[5] if len(parts) > 5 else "{}"
        return {
            "phone": phone,
            "pin": pin,
            "balance": balance,
            "vector_clock": vector_clock
        }
    return None


def create_account_in_server2(account):
    """Create account directly in Server 2 database"""
    try:
        conn = sqlite3.connect(SERVER2_DB)
        
        # Check if account exists
        cursor = conn.execute("SELECT phone FROM accounts WHERE phone = ?", (account["phone"],))
        if cursor.fetchone():
            print(f"  ⚠ Account {account['phone']} already exists, skipping")
            conn.close()
            return True
        
        # Insert account
        conn.execute(
            "INSERT INTO accounts (phone, pin, balance, vector_clock, physical_timestamp, last_modified_by) VALUES (?, ?, ?, ?, ?, ?)",
            (account["phone"], account["pin"], account["balance"], account["vector_clock"], time.time(), 1)
        )
        conn.commit()
        conn.close()
        
        print(f"  ✓ Created account {account['phone']} with balance {account['balance']}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error creating account: {e}")
        return False


def main():
    print("=" * 60)
    print("SYNC DATA FROM SERVER 1 TO SERVER 2")
    print("=" * 60)
    
    print("\n⚠ WARNING: Make sure Server 2 is RUNNING before continuing!")
    print("  This script will:")
    print("  1. Connect to Server 1 to get account data")
    print("  2. Insert accounts directly into Server 2 database")
    print("\n  Press Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
    
    # Get account details from user
    print("\n" + "=" * 60)
    print("ACCOUNT TO SYNC")
    print("=" * 60)
    
    phone = input("\nEnter phone number: ").strip()
    pin = input("Enter PIN: ").strip()
    
    print(f"\nFetching account {phone} from Server 1...")
    account = get_account_from_server1(phone, pin)
    
    if not account:
        print("✗ Could not fetch account from Server 1")
        print("  Possible reasons:")
        print("  - Invalid phone number or PIN")
        print("  - Server 1 is not running")
        print("  - Network connectivity issue")
        sys.exit(1)
    
    print(f"✓ Found account on Server 1:")
    print(f"  Phone: {account['phone']}")
    print(f"  Balance: {account['balance']}")
    
    print(f"\nCreating account in Server 2 database...")
    success = create_account_in_server2(account)
    
    if success:
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print("\nAccount synced to Server 2!")
        print("\nYou can now:")
        print("  1. Login on Server 2 with the same credentials")
        print("  2. Check balance - should match Server 1")
        print("  3. Make transactions - they will replicate!")
        print("=" * 60)
    else:
        print("\n✗ Failed to sync account")
        sys.exit(1)


if __name__ == "__main__":
    main()
