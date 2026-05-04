#!/usr/bin/env python3
"""
Peer-to-Peer Sync - All servers share data with each other
Each server contributes its unique data to all other servers
True distributed peer-to-peer synchronization
"""

import sqlite3
import sys
import os
import json
from collections import defaultdict

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


def peer_to_peer_sync():
    """Peer-to-peer sync - all servers share data with each other"""
    
    print("=" * 80)
    print("PEER-TO-PEER SYNC - ALL SERVERS SHARE DATA")
    print("=" * 80)
    
    # Get all servers
    servers = get_all_servers()
    
    if not servers:
        print("\n✗ No servers found!")
        print("  Make sure servers.json exists or database files are in data/ folder")
        sys.exit(1)
    
    # Filter servers that have databases
    active_servers = []
    for server in servers:
        server_id = server["id"]
        db_path = f"data/server_{server_id}.db"
        if os.path.exists(db_path):
            active_servers.append(server)
    
    if len(active_servers) < 2:
        print("\n✗ Need at least 2 servers to sync!")
        sys.exit(1)
    
    print(f"\nFound {len(active_servers)} server(s) with databases:")
    for server in active_servers:
        server_id = server["id"]
        db_path = f"data/server_{server_id}.db"
        print(f"  ✓ Server {server_id}: {db_path}")
    
    print("\n⚠ PEER-TO-PEER SYNC:")
    print("  - All servers are equal peers (no master)")
    print("  - Each server shares its data with all others")
    print("  - Conflicts resolved using Last-Writer-Wins (newest timestamp)")
    print("  - All servers will have the union of all data")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
    
    # Step 1: Collect all accounts from all servers
    print("\n" + "=" * 80)
    print("STEP 1: COLLECTING DATA FROM ALL SERVERS")
    print("=" * 80)
    
    all_accounts = {}  # phone -> {data, source_server}
    
    for server in active_servers:
        server_id = server["id"]
        db_path = f"data/server_{server_id}.db"
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.execute(
                "SELECT phone, pin, balance, vector_clock, physical_timestamp, last_modified_by FROM accounts"
            )
            
            count = 0
            for row in cursor.fetchall():
                phone, pin, balance, vector_clock, physical_timestamp, last_modified_by = row
                
                # Check if we already have this account
                if phone in all_accounts:
                    # Conflict! Use Last-Writer-Wins (newest timestamp)
                    existing_ts = all_accounts[phone]["physical_timestamp"]
                    if physical_timestamp > existing_ts:
                        # This version is newer
                        all_accounts[phone] = {
                            "pin": pin,
                            "balance": balance,
                            "vector_clock": vector_clock,
                            "physical_timestamp": physical_timestamp,
                            "last_modified_by": last_modified_by,
                            "source_server": server_id
                        }
                        print(f"  Server {server_id}: {phone} (balance={balance}) [NEWER - USING THIS]")
                    else:
                        print(f"  Server {server_id}: {phone} (balance={balance}) [OLDER - SKIPPING]")
                else:
                    # New account
                    all_accounts[phone] = {
                        "pin": pin,
                        "balance": balance,
                        "vector_clock": vector_clock,
                        "physical_timestamp": physical_timestamp,
                        "last_modified_by": last_modified_by,
                        "source_server": server_id
                    }
                    print(f"  Server {server_id}: {phone} (balance={balance}) [NEW]")
                
                count += 1
            
            conn.close()
            print(f"\n✓ Server {server_id}: Collected {count} account(s)")
            
        except Exception as e:
            print(f"✗ Error reading Server {server_id}: {e}")
    
    print(f"\n✓ Total unique accounts collected: {len(all_accounts)}")
    
    # Step 2: Distribute merged data to all servers
    print("\n" + "=" * 80)
    print("STEP 2: DISTRIBUTING MERGED DATA TO ALL SERVERS")
    print("=" * 80)
    
    for server in active_servers:
        server_id = server["id"]
        db_path = f"data/server_{server_id}.db"
        
        print(f"\n{'=' * 80}")
        print(f"SYNCING SERVER {server_id}")
        print(f"{'=' * 80}")
        
        try:
            conn = sqlite3.connect(db_path)
            
            # Get existing accounts
            cursor = conn.execute("SELECT phone FROM accounts")
            existing_phones = set(row[0] for row in cursor.fetchall())
            
            print(f"  Current accounts: {len(existing_phones)}")
            
            added = 0
            updated = 0
            skipped = 0
            
            for phone, data in all_accounts.items():
                if phone in existing_phones:
                    # Update existing account
                    conn.execute(
                        "UPDATE accounts SET pin = ?, balance = ?, vector_clock = ?, physical_timestamp = ?, last_modified_by = ? WHERE phone = ?",
                        (data["pin"], data["balance"], data["vector_clock"], data["physical_timestamp"], data["last_modified_by"], phone)
                    )
                    updated += 1
                    source = data["source_server"]
                    print(f"    ✓ Updated: {phone} (balance={data['balance']}) [from Server {source}]")
                else:
                    # Insert new account
                    conn.execute(
                        "INSERT INTO accounts (phone, pin, balance, vector_clock, physical_timestamp, last_modified_by) VALUES (?, ?, ?, ?, ?, ?)",
                        (phone, data["pin"], data["balance"], data["vector_clock"], data["physical_timestamp"], data["last_modified_by"])
                    )
                    added += 1
                    source = data["source_server"]
                    print(f"    ✓ Added: {phone} (balance={data['balance']}) [from Server {source}]")
            
            conn.commit()
            
            # Verify
            cursor = conn.execute("SELECT COUNT(*) FROM accounts")
            final_count = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"\n  ✓ Server {server_id} sync complete:")
            print(f"    - Added: {added} account(s)")
            print(f"    - Updated: {updated} account(s)")
            print(f"    - Total: {final_count} account(s)")
            
            if final_count == len(all_accounts):
                print(f"  ✓ Server {server_id} has all {len(all_accounts)} account(s)!")
            else:
                print(f"  ⚠ Warning: Server {server_id} has {final_count} accounts, expected {len(all_accounts)}")
        
        except Exception as e:
            print(f"  ✗ Error syncing Server {server_id}: {e}")
    
    # Step 3: Summary
    print("\n" + "=" * 80)
    print("PEER-TO-PEER SYNC COMPLETE!")
    print("=" * 80)
    
    print(f"\n✓ Servers synced: {len(active_servers)}")
    print(f"✓ Total accounts: {len(all_accounts)}")
    print(f"✓ All servers now have {len(all_accounts)} account(s)")
    
    # Show data sources
    print("\n" + "=" * 80)
    print("DATA SOURCES (Which server contributed each account)")
    print("=" * 80)
    
    sources = defaultdict(list)
    for phone, data in all_accounts.items():
        sources[data["source_server"]].append(phone)
    
    for server_id in sorted(sources.keys()):
        phones = sources[server_id]
        print(f"\nServer {server_id} contributed {len(phones)} account(s):")
        for phone in sorted(phones):
            balance = all_accounts[phone]["balance"]
            print(f"  - {phone} (balance={balance})")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("\n1. Restart all servers:")
    for server in active_servers:
        server_id = server["id"]
        print(f"   python server.py {server_id}")
    
    print("\n2. Test with client:")
    print("   python client.py")
    
    print("\n3. All servers now have identical data!")
    print("   Any account can be accessed from any server")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    peer_to_peer_sync()
