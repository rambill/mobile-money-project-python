#!/usr/bin/env python3
"""
Admin Console for Distributed Mobile Money System
Provides server monitoring, consistency checks, and integration tests
"""

import socket
import time
import json
import sys
import sqlite3
import os
from typing import Dict, List

import config


class AdminConsole:
    """Admin tools for monitoring and testing"""
    
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(2.0)
    
    def discover_servers(self) -> List[Dict]:
        """Discover all running servers"""
        discovery_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        discovery_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        discovery_sock.settimeout(2.0)
        
        discovery_sock.sendto(b"DISCOVER", ('<broadcast>', config.DISCOVERY_PORT))
        
        servers = []
        start_time = time.time()
        
        while time.time() - start_time < 2.0:
            try:
                data, addr = discovery_sock.recvfrom(config.MAX_PACKET_SIZE)
                server_info = json.loads(data.decode())
                servers.append(server_info)
            except socket.timeout:
                break
            except Exception:
                pass
        
        discovery_sock.close()
        return servers
    
    def show_status(self):
        """Show status of all servers"""
        print("\n" + "="*80)
        print("  DISTRIBUTED MOBILE MONEY - SERVER STATUS")
        print("="*80)
        
        servers = self.discover_servers()
        
        if not servers:
            print("\n✗ No servers found!")
            print("  Make sure servers are running: python server.py <id>")
            return
        
        print(f"\n✓ Found {len(servers)} active server(s):\n")
        
        for server in servers:
            print(f"  Server {server['id']}: {server['name']}")
            print(f"    Host: {server['host']}:{server['port']}")
            print(f"    Load: {server.get('load', 0)} requests")
            
            # Check database
            db_path = os.path.join(config.DB_DIR, config.DB_NAME_TEMPLATE.format(server['id']))
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.execute("SELECT COUNT(*) FROM accounts")
                    account_count = cursor.fetchone()[0]
                    
                    cursor = conn.execute("SELECT COUNT(*) FROM transactions")
                    txn_count = cursor.fetchone()[0]
                    
                    print(f"    Accounts: {account_count}")
                    print(f"    Transactions: {txn_count}")
                    
                    conn.close()
                except Exception as e:
                    print(f"    Database error: {e}")
            else:
                print(f"    Database: Not found")
            
            print()
    
    def check_consistency(self):
        """Check replication consistency across servers"""
        print("\n" + "="*80)
        print("  REPLICATION CONSISTENCY CHECK")
        print("="*80)
        
        servers = self.discover_servers()
        
        if len(servers) < 2:
            print("\n✗ Need at least 2 servers for consistency check")
            return
        
        print(f"\nChecking consistency across {len(servers)} servers...\n")
        
        # Collect account data from all servers
        server_data = {}
        
        for server in servers:
            db_path = os.path.join(config.DB_DIR, config.DB_NAME_TEMPLATE.format(server['id']))
            
            if not os.path.exists(db_path):
                print(f"✗ Server {server['id']}: Database not found")
                continue
            
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute("SELECT phone, balance, vector_clock FROM accounts ORDER BY phone")
                accounts = {}
                
                for row in cursor.fetchall():
                    accounts[row['phone']] = {
                        'balance': row['balance'],
                        'vector_clock': row['vector_clock']
                    }
                
                server_data[server['id']] = accounts
                conn.close()
                
                print(f"✓ Server {server['id']}: {len(accounts)} accounts")
                
            except Exception as e:
                print(f"✗ Server {server['id']}: Error - {e}")
        
        if len(server_data) < 2:
            print("\n✗ Not enough server data to compare")
            return
        
        # Compare accounts across servers
        print("\nComparing account data...\n")
        
        all_phones = set()
        for accounts in server_data.values():
            all_phones.update(accounts.keys())
        
        inconsistencies = []
        
        for phone in sorted(all_phones):
            balances = {}
            
            for server_id, accounts in server_data.items():
                if phone in accounts:
                    balances[server_id] = accounts[phone]['balance']
            
            # Check if all balances match
            unique_balances = set(balances.values())
            
            if len(unique_balances) > 1:
                inconsistencies.append({
                    'phone': phone,
                    'balances': balances
                })
        
        if inconsistencies:
            print(f"✗ Found {len(inconsistencies)} inconsistencies:\n")
            
            for item in inconsistencies:
                print(f"  Account: {item['phone']}")
                for server_id, balance in item['balances'].items():
                    print(f"    Server {server_id}: UGX {balance:,.2f}")
                print()
        else:
            print(f"✓ All {len(all_phones)} accounts are consistent across servers!")
    
    def run_integration_tests(self):
        """Run integration tests"""
        print("\n" + "="*80)
        print("  INTEGRATION TESTS")
        print("="*80)
        
        servers = self.discover_servers()
        
        if not servers:
            print("\n✗ No servers found!")
            return
        
        print(f"\nRunning tests against {len(servers)} server(s)...\n")
        
        # Test 1: Account registration
        print("Test 1: Account Registration")
        test_phone = f"256700{int(time.time()) % 1000000}"
        test_pin = "1234"
        
        server = servers[0]
        message = f"REQ|test1|REGISTER|{test_phone}|{test_pin}"
        
        try:
            self.socket.sendto(
                message.encode()[:config.MAX_PACKET_SIZE],
                (server['host'], server['port'])
            )
            
            data, _ = self.socket.recvfrom(config.MAX_PACKET_SIZE)
            response = data.decode().strip()
            
            if "OK" in response:
                print(f"  ✓ Account {test_phone} registered successfully")
            else:
                print(f"  ✗ Registration failed: {response}")
                return
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return
        
        # Wait for replication
        time.sleep(2)
        
        # Test 2: Deposit
        print("\nTest 2: Deposit Money")
        message = f"REQ|test2|DEPOSIT|{test_phone}|{test_pin}|10000"
        
        try:
            self.socket.sendto(
                message.encode()[:config.MAX_PACKET_SIZE],
                (server['host'], server['port'])
            )
            
            data, _ = self.socket.recvfrom(config.MAX_PACKET_SIZE)
            response = data.decode().strip()
            
            if "OK" in response:
                print(f"  ✓ Deposited UGX 10,000")
            else:
                print(f"  ✗ Deposit failed: {response}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        # Wait for replication
        time.sleep(2)
        
        # Test 3: Check balance on different server
        if len(servers) > 1:
            print("\nTest 3: Read-Your-Writes (Different Server)")
            server2 = servers[1]
            message = f"REQ|test3|BALANCE|{test_phone}|{test_pin}"
            
            try:
                self.socket.sendto(
                    message.encode()[:config.MAX_PACKET_SIZE],
                    (server2['host'], server2['port'])
                )
                
                data, _ = self.socket.recvfrom(config.MAX_PACKET_SIZE)
                response = data.decode().strip()
                
                if "OK" in response and "10000" in response:
                    print(f"  ✓ Balance replicated correctly to Server {server2['id']}")
                else:
                    print(f"  ✗ Balance mismatch: {response}")
            except Exception as e:
                print(f"  ✗ Error: {e}")
        
        # Test 4: Withdraw
        print("\nTest 4: Withdraw Money")
        message = f"REQ|test4|WITHDRAW|{test_phone}|{test_pin}|3000"
        
        try:
            self.socket.sendto(
                message.encode()[:config.MAX_PACKET_SIZE],
                (server['host'], server['port'])
            )
            
            data, _ = self.socket.recvfrom(config.MAX_PACKET_SIZE)
            response = data.decode().strip()
            
            if "OK" in response and "7000" in response:
                print(f"  ✓ Withdrew UGX 3,000, balance: UGX 7,000")
            else:
                print(f"  ✗ Withdrawal failed: {response}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        # Test 5: Insufficient balance
        print("\nTest 5: Insufficient Balance Check")
        message = f"REQ|test5|WITHDRAW|{test_phone}|{test_pin}|10000"
        
        try:
            self.socket.sendto(
                message.encode()[:config.MAX_PACKET_SIZE],
                (server['host'], server['port'])
            )
            
            data, _ = self.socket.recvfrom(config.MAX_PACKET_SIZE)
            response = data.decode().strip()
            
            if "ERR" in response and "Insufficient" in response:
                print(f"  ✓ Correctly rejected insufficient balance")
            else:
                print(f"  ✗ Should have rejected: {response}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        print("\n" + "="*80)
        print("Tests completed!")
        print("="*80)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python admin.py status    - Show server status")
        print("  python admin.py sync      - Check replication consistency")
        print("  python admin.py test      - Run integration tests")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    admin = AdminConsole()
    
    if command == "status":
        admin.show_status()
    elif command == "sync":
        admin.check_consistency()
    elif command == "test":
        admin.run_integration_tests()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
