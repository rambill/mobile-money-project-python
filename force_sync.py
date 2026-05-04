#!/usr/bin/env python3
"""
Force sync all servers from Server 1 (master)
Copies all accounts from Server 1 to all other servers
"""

import sqlite3
import sys
import os
import json

def get_all_servers():
    """Get list of all servers from config"""
    servers = []
    
    # Try to load from servers.json
    if os.path.exists("servers.json"):
        try:
            with open("servers.json", "r") as f:
                data = json.load(f)
                servers = data.get("servers", [])
        except Exception as e:
            print(f"Warning: Could not load servers.json: {e}")
    
    if not servers:
        # Fallback: check for database files
        if os.path.exists("data"):
            for filename in os.listdir("data"):
                if filename.startswith("server_") and filename.endswith(".db"):
                    server_id = int(filename.replace("server_", "").replace(".db", ""))
                    servers.append({"id": server_id})
    
    return sorted(servers, key=lambda s: s["id"])


def force_sync_all():
    """Force sync all servers from Server 1"""
    
    print("=" * 80)
    print("FORCE SYNC ALL SERVERS FROM SERVER 1 (MASTER)")
    print("=" * 80)
    
    # Get all servers
    servers = get_all_servers()
    
    if not servers:
        print("\n✗ No servers found!")
        print("  Make sure servers.json exists or database files are in data/ folder")
        sys.exit(1)
    
    print(f"\nFound {len(servers)} server(s):")
    for server in servers:
        server_id = server["id"]
        db_path = f"data/server_{server_id}.db"
        exists = "✓" if os.path.exists(db_path) else "✗"
        print(f"  {exists} Server {server_id}: {db_path}")
    
    # Check if Server 1 exists
    if not os.path.exists("data/server_1.db"):
        print("\n✗ Server 1 database not found!")
        print("  Server 1 is the master - it must exist")
        sys.exit(1)
    
    print("\n⚠ WARNING: This will update ALL servers to match Server 1!")
    print("  - Server 1 is the master (source of truth)")
    print("  - All other servers will be updated to match Server 1")
    print("  - Missing accounts will be added")
    print("  - Different balances will be updated")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
    
    # Connect to Server 1 (master)
    try:
        conn1 = sqlite3.connect("data/server_1.db")
        print("\n✓ Connected to Server 1 (master)")
        
        # Get all accounts from Server 1
        cursor1 = conn1.execute(
            "SELECT phone, pin, balance, vector_clock, physical_timestamp, last_modified_by FROM accounts"
        )
        master_accounts = cursor1.fetchall()
        
        print(f"✓ Found {len(master_accounts)} account(s) on Server 1 (master)")
        
        # Sync to each other server
        total_servers_synced = 0
        
        for server in servers:
            server_id = server["id"]
            
            if server_id == 1:
                continue  # Skip Server 1 (it's the master)
            
            db_path = f"data/server_{server_id}.db"
            
            if not os.path.exists(db_path):
                print(f"\n⚠ Skipping Server {server_id}: database not found")
                continue
            
            print(f"\n{'=' * 80}")
            print(f"SYNCING SERVER {server_id}")
            print(f"{'=' * 80}")
            
            try:
                # Connect to target server
                conn_target = sqlite3.connect(db_path)
                
                # Get existing accounts
                cursor_target = conn_target.execute("SELECT phone FROM accounts")
                target_phones = set(row[0] for row in cursor_target.fetchall())
                
                print(f"  Current accounts on Server {server_id}: {len(target_phones)}")
                
                # Sync each account
                added = 0
                updated = 0
                
                for row in master_accounts:
                    phone, pin, balance, vector_clock, physical_timestamp, last_modified_by = row
                    
                    if phone in target_phones:
                        # Update existing account
                        conn_target.execute(
                            "UPDATE accounts SET pin = ?, balance = ?, vector_clock = ?, physical_timestamp = ?, last_modified_by = ? WHERE phone = ?",
                            (pin, balance, vector_clock, physical_timestamp, last_modified_by, phone)
                        )
                        updated += 1
                        print(f"    ✓ Updated: {phone} (balance={balance})")
                    else:
                        # Insert new account
                        conn_target.execute(
                            "INSERT INTO accounts (phone, pin, balance, vector_clock, physical_timestamp, last_modified_by) VALUES (?, ?, ?, ?, ?, ?)",
                            (phone, pin, balance, vector_clock, physical_timestamp, last_modified_by)
                        )
                        added += 1
                        print(f"    ✓ Added: {phone} (balance={balance})")
                
                conn_target.commit()
                
                # Verify
                cursor_target = conn_target.execute("SELECT COUNT(*) FROM accounts")
                count = cursor_target.fetchone()[0]
                
                print(f"\n  ✓ Server {server_id} sync complete:")
                print(f"    - Added: {added} account(s)")
                print(f"    - Updated: {updated} account(s)")
                print(f"    - Total: {count} account(s)")
                
                if count == len(master_accounts):
                    print(f"  ✓ Server {server_id} matches Server 1!")
                else:
                    print(f"  ⚠ Warning: Server {server_id} has {count} accounts, Server 1 has {len(master_accounts)}")
                
                conn_target.close()
                total_servers_synced += 1
                
            except Exception as e:
                print(f"  ✗ Error syncing Server {server_id}: {e}")
        
        conn1.close()
        
        print("\n" + "=" * 80)
        print("SYNC COMPLETE!")
        print("=" * 80)
        print(f"\n✓ Master: Server 1 ({len(master_accounts)} accounts)")
        print(f"✓ Synced: {total_servers_synced} server(s)")
        print(f"✓ All servers now have {len(master_accounts)} account(s)")
        
        print("\n" + "=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print("\n1. Restart all servers:")
        for server in servers:
            server_id = server["id"]
            if os.path.exists(f"data/server_{server_id}.db"):
                print(f"   python server.py {server_id}")
        
        print("\n2. Verify sync:")
        print("   python compare_databases.py")
        
        print("\n3. Test with client:")
        print("   python client.py")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    force_sync_all()
