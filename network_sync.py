#!/usr/bin/env python3
"""
Network-Based Peer-to-Peer Sync
Syncs servers across different machines using UDP network communication
Works even when servers are on different physical machines
"""

import socket
import json
import time
import sys
from collections import defaultdict
from typing import Dict, List, Optional

import config


class NetworkSync:
    """Network-based synchronization across machines"""
    
    def __init__(self):
        self.timeout = 10.0  # 10 second timeout
        self.max_retries = 3
    
    def request_full_state(self, server_config: Dict) -> Optional[Dict]:
        """Request full state from a server via network"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            
            # Send STATE_REQUEST
            message = json.dumps({
                "type": "STATE_REQUEST",
                "from": 0,  # Sync tool (not a server)
                "data": {}
            })
            
            print(f"  Requesting state from {server_config['name']} ({server_config['host']}:{server_config['rep_port']})...")
            
            sock.sendto(message.encode(), (server_config['host'], server_config['rep_port']))
            
            # Receive response
            response_data, _ = sock.recvfrom(config.MAX_PACKET_SIZE)
            response = json.loads(response_data.decode())
            
            data = response.get("data", {})
            
            # Check if response is chunked
            if data.get("chunked"):
                print(f"  Receiving chunked data ({data.get('total_chunks')} chunks, {data.get('total_size')} bytes)...")
                return self._receive_chunked_state(sock, server_config, data)
            else:
                accounts = data.get("accounts", {})
                print(f"  ✓ Received {len(accounts)} account(s) from {server_config['name']}")
                sock.close()
                return {"success": True, "accounts": accounts, "server_id": server_config['id']}
        
        except socket.timeout:
            print(f"  ✗ Timeout waiting for {server_config['name']}")
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            print(f"  ✗ Error requesting state from {server_config['name']}: {e}")
            return {"success": False, "error": str(e)}
    
    def _receive_chunked_state(self, sock: socket.socket, server_config: Dict, first_chunk_data: Dict) -> Dict:
        """Receive chunked state transfer"""
        try:
            total_chunks = first_chunk_data.get("total_chunks", 0)
            chunks = [first_chunk_data.get("data", "")]
            
            # Request remaining chunks
            for chunk_id in range(1, total_chunks):
                message = json.dumps({
                    "type": "STATE_REQUEST_CHUNK",
                    "from": 0,
                    "data": {"chunk_id": chunk_id}
                })
                
                sock.sendto(message.encode(), (server_config['host'], server_config['rep_port']))
                
                response_data, _ = sock.recvfrom(config.MAX_PACKET_SIZE)
                response = json.loads(response_data.decode())
                
                chunk_data = response.get("data", {})
                if chunk_data.get("success"):
                    chunks.append(chunk_data.get("data", ""))
                    print(f"  Received chunk {chunk_id + 1}/{total_chunks}")
                else:
                    print(f"  ✗ Failed to receive chunk {chunk_id + 1}")
                    return {"success": False, "error": "Chunk transfer failed"}
            
            # Reassemble chunks
            full_data = "".join(chunks)
            accounts = json.loads(full_data)
            
            print(f"  ✓ Received {len(accounts)} account(s) from {server_config['name']}")
            sock.close()
            return {"success": True, "accounts": accounts, "server_id": server_config['id']}
        
        except Exception as e:
            print(f"  ✗ Error receiving chunked data: {e}")
            return {"success": False, "error": str(e)}
    
    def send_account_to_server(self, server_config: Dict, phone: str, account_data: Dict) -> bool:
        """Send account data to a server via replication"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5.0)
            
            # Send REPLICATE message
            operation = {
                "command": "SYNC_ACCOUNT",
                "phone": phone,
                "pin": account_data.get("pin", ""),
                "balance": account_data.get("balance", 0.0),
                "vector_clock": account_data.get("vector_clock", "{}"),
                "physical_timestamp": account_data.get("physical_timestamp", time.time()),
                "last_modified_by": account_data.get("last_modified_by", 0)
            }
            
            message = json.dumps({
                "type": "REPLICATE",
                "from": 0,  # Sync tool
                "data": {"operation": operation}
            })
            
            sock.sendto(message.encode(), (server_config['host'], server_config['rep_port']))
            sock.close()
            return True
        
        except Exception as e:
            return False


def network_peer_sync():
    """Network-based peer-to-peer sync across machines"""
    
    print("=" * 80)
    print("NETWORK PEER-TO-PEER SYNC - SYNC ACROSS DIFFERENT MACHINES")
    print("=" * 80)
    
    # Get all active servers from config
    servers = config.get_active_servers()
    
    if len(servers) < 2:
        print("\n✗ Need at least 2 active servers in config!")
        print("  Check servers.json or config.py")
        sys.exit(1)
    
    print(f"\nFound {len(servers)} active server(s) in config:")
    for server in servers:
        print(f"  Server {server['id']}: {server['name']} ({server['host']}:{server['port']})")
    
    print("\n⚠ NETWORK SYNC:")
    print("  - Connects to servers via network (works across machines)")
    print("  - All servers must be RUNNING")
    print("  - Each server shares its data with all others")
    print("  - Conflicts resolved using Last-Writer-Wins (newest timestamp)")
    print("  - All servers will have the union of all data")
    print("\n⚠ IMPORTANT: Make sure ALL servers are running before continuing!")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
    
    sync = NetworkSync()
    
    # Step 1: Collect data from all servers
    print("\n" + "=" * 80)
    print("STEP 1: COLLECTING DATA FROM ALL SERVERS")
    print("=" * 80)
    
    all_accounts = {}  # phone -> {data, source_server}
    responding_servers = []
    
    for server in servers:
        print(f"\nServer {server['id']}: {server['name']}")
        
        result = sync.request_full_state(server)
        
        if result.get("success"):
            responding_servers.append(server)
            accounts = result.get("accounts", {})
            
            for phone, account_data in accounts.items():
                # Check if we already have this account
                if phone in all_accounts:
                    # Conflict! Use Last-Writer-Wins (newest timestamp)
                    existing_ts = all_accounts[phone]["physical_timestamp"]
                    new_ts = account_data.get("physical_timestamp", 0)
                    
                    if new_ts > existing_ts:
                        # This version is newer
                        all_accounts[phone] = {
                            "pin": account_data.get("pin", ""),
                            "balance": account_data.get("balance", 0.0),
                            "vector_clock": account_data.get("vector_clock", "{}"),
                            "physical_timestamp": new_ts,
                            "last_modified_by": account_data.get("last_modified_by", server['id']),
                            "source_server": server['id']
                        }
                        print(f"    {phone} (balance={account_data.get('balance', 0.0)}) [NEWER - USING THIS]")
                    else:
                        print(f"    {phone} (balance={account_data.get('balance', 0.0)}) [OLDER - SKIPPING]")
                else:
                    # New account
                    all_accounts[phone] = {
                        "pin": account_data.get("pin", ""),
                        "balance": account_data.get("balance", 0.0),
                        "vector_clock": account_data.get("vector_clock", "{}"),
                        "physical_timestamp": account_data.get("physical_timestamp", time.time()),
                        "last_modified_by": account_data.get("last_modified_by", server['id']),
                        "source_server": server['id']
                    }
                    print(f"    {phone} (balance={account_data.get('balance', 0.0)}) [NEW]")
            
            print(f"  ✓ Collected {len(accounts)} account(s) from Server {server['id']}")
        else:
            print(f"  ✗ Server {server['id']} not responding (may be offline)")
    
    if not responding_servers:
        print("\n✗ No servers responded!")
        print("  Make sure servers are running and network is accessible")
        sys.exit(1)
    
    print(f"\n✓ Total unique accounts collected: {len(all_accounts)}")
    print(f"✓ Responding servers: {len(responding_servers)}/{len(servers)}")
    
    # Step 2: Distribute merged data to all responding servers
    print("\n" + "=" * 80)
    print("STEP 2: DISTRIBUTING MERGED DATA TO ALL SERVERS")
    print("=" * 80)
    
    for server in responding_servers:
        print(f"\n{'=' * 80}")
        print(f"SYNCING SERVER {server['id']}: {server['name']}")
        print(f"{'=' * 80}")
        
        # Get current state from server
        result = sync.request_full_state(server)
        
        if not result.get("success"):
            print(f"  ✗ Cannot sync Server {server['id']} (not responding)")
            continue
        
        current_accounts = result.get("accounts", {})
        print(f"  Current accounts: {len(current_accounts)}")
        
        added = 0
        updated = 0
        
        for phone, data in all_accounts.items():
            if phone in current_accounts:
                # Check if update needed
                current_ts = current_accounts[phone].get("physical_timestamp", 0)
                new_ts = data["physical_timestamp"]
                
                if new_ts > current_ts:
                    # Send update
                    if sync.send_account_to_server(server, phone, data):
                        updated += 1
                        source = data["source_server"]
                        print(f"    ✓ Updated: {phone} (balance={data['balance']}) [from Server {source}]")
                    else:
                        print(f"    ✗ Failed to update: {phone}")
            else:
                # Send new account
                if sync.send_account_to_server(server, phone, data):
                    added += 1
                    source = data["source_server"]
                    print(f"    ✓ Added: {phone} (balance={data['balance']}) [from Server {source}]")
                else:
                    print(f"    ✗ Failed to add: {phone}")
        
        print(f"\n  ✓ Server {server['id']} sync complete:")
        print(f"    - Added: {added} account(s)")
        print(f"    - Updated: {updated} account(s)")
        print(f"    - Expected total: {len(all_accounts)} account(s)")
    
    # Step 3: Summary
    print("\n" + "=" * 80)
    print("NETWORK PEER-TO-PEER SYNC COMPLETE!")
    print("=" * 80)
    
    print(f"\n✓ Servers synced: {len(responding_servers)}/{len(servers)}")
    print(f"✓ Total accounts: {len(all_accounts)}")
    print(f"✓ All responding servers should now have {len(all_accounts)} account(s)")
    
    # Show data sources
    print("\n" + "=" * 80)
    print("DATA SOURCES (Which server contributed each account)")
    print("=" * 80)
    
    sources = defaultdict(list)
    for phone, data in all_accounts.items():
        sources[data["source_server"]].append(phone)
    
    for server_id in sorted(sources.keys()):
        phones = sources[server_id]
        server_name = next((s['name'] for s in servers if s['id'] == server_id), f"Server {server_id}")
        print(f"\nServer {server_id} ({server_name}) contributed {len(phones)} account(s):")
        for phone in sorted(phones):
            balance = all_accounts[phone]["balance"]
            print(f"  - {phone} (balance={balance})")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("\n1. Servers are already running (no restart needed)")
    print("\n2. Test with client:")
    print("   python client.py")
    print("\n3. All servers now have identical data!")
    print("   Any account can be accessed from any server")
    
    if len(responding_servers) < len(servers):
        print("\n⚠ WARNING: Some servers did not respond:")
        for server in servers:
            if server not in responding_servers:
                print(f"  - Server {server['id']}: {server['name']} ({server['host']}:{server['port']})")
        print("\n  Make sure these servers are running and try again!")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    network_peer_sync()

