#!/usr/bin/env python3
"""
Mobile Money Client
Discovers servers, manages sessions, and enforces client-centric consistency
"""

import socket
import time
import json
import sys
from typing import Dict, List, Optional, Tuple

import config
from distributed import VectorClock


class MobileMoneyClient:
    """Mobile money client with consistency guarantees"""
    
    def __init__(self):
        self.servers = []
        self.current_server = None
        self.session_id = int(time.time() * 1000)
        self.request_counter = 0
        
        # Client-centric consistency state
        self.last_write_server = None
        self.last_write_time = 0
        self.last_write_vc = VectorClock()
        self.last_read_vc = VectorClock()
        
        # Cache
        self.cache = {}
        self.cache_expiry = {}
    
    def discover_servers(self) -> List[Dict]:
        """Discover available servers via UDP broadcast and servers.json"""
        print("Discovering servers...")
        
        servers = []
        
        # Method 1: Try UDP broadcast discovery
        try:
            discovery_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            discovery_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            discovery_sock.settimeout(2.0)
            
            # Send discovery broadcast
            discovery_sock.sendto(b"DISCOVER", ('<broadcast>', config.DISCOVERY_PORT))
            
            start_time = time.time()
            
            while time.time() - start_time < 2.0:
                try:
                    data, addr = discovery_sock.recvfrom(config.MAX_PACKET_SIZE)
                    server_info = json.loads(data.decode())
                    
                    # Measure latency
                    latency = (time.time() - start_time) * 1000  # ms
                    server_info['latency'] = latency
                    server_info['addr'] = addr
                    
                    servers.append(server_info)
                except socket.timeout:
                    break
                except Exception as e:
                    pass
            
            discovery_sock.close()
        except Exception as e:
            print(f"Broadcast discovery failed: {e}")
        
        # Method 2: Load from servers.json (fallback or supplement)
        try:
            import os
            if os.path.exists("servers.json"):
                with open("servers.json", "r") as f:
                    data = json.load(f)
                    config_servers = data.get("servers", [])
                    
                    for server in config_servers:
                        if not server.get("active", True):
                            continue
                        
                        # Check if already discovered via broadcast
                        server_id = server.get("id")
                        already_found = any(s.get("id") == server_id for s in servers)
                        
                        if not already_found:
                            # Try to ping this server
                            try:
                                test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                                test_sock.settimeout(1.0)
                                
                                # Send a simple ping
                                req_id = f"ping_{time.time()}"
                                message = f"REQ|{req_id}|BALANCE|0000000000|0000"
                                
                                start = time.time()
                                test_sock.sendto(message.encode(), (server['host'], server['port']))
                                
                                # Wait for response
                                data, addr = test_sock.recvfrom(config.MAX_PACKET_SIZE)
                                latency = (time.time() - start) * 1000
                                
                                test_sock.close()
                                
                                # Add to servers list
                                servers.append({
                                    "id": server['id'],
                                    "name": server.get('name', f"Server {server['id']}"),
                                    "host": server['host'],
                                    "port": server['port'],
                                    "latency": latency,
                                    "addr": (server['host'], server['port'])
                                })
                                print(f"  Found Server {server['id']} via config: {server.get('name', 'Unknown')}")
                            except:
                                pass
        except Exception as e:
            print(f"Config discovery failed: {e}")
        
        # Sort by latency
        servers.sort(key=lambda s: s.get('latency', 999999))
        
        self.servers = servers
        
        if servers:
            print(f"Found {len(servers)} server(s):")
            for i, server in enumerate(servers, 1):
                print(f"  {i}. {server['name']} - {server['latency']:.1f}ms")
            
            # Select nearest server
            self.current_server = servers[0]
            print(f"\nConnected to: {self.current_server['name']}")
        else:
            print("No servers found!")
        
        return servers
    
    def _send_request(self, command: str, *args) -> Optional[Dict]:
        """Send RPC request to server"""
        if not self.current_server:
            print("Not connected to any server!")
            return None
        
        self.request_counter += 1
        req_id = f"{self.session_id}_{self.request_counter}"
        
        # Build request message
        message = f"REQ|{req_id}|{command}|" + "|".join(str(arg) for arg in args)
        
        # Create a fresh socket for each request to avoid connection issues
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(config.UDP_TIMEOUT_SEC)
        
        try:
            # Send request
            sock.sendto(
                message.encode()[:config.MAX_PACKET_SIZE],
                (self.current_server['host'], self.current_server['port'])
            )
            
            # Wait for response
            data, _ = sock.recvfrom(config.MAX_PACKET_SIZE)
            response = data.decode().strip()
            
            # Close socket
            sock.close()
            
            # Parse response: RES|id|status|message|balance|vector_clock
            parts = response.split('|')
            
            if len(parts) >= 6:
                return {
                    "id": parts[1],
                    "status": parts[2],
                    "message": parts[3],
                    "balance": float(parts[4]),
                    "vector_clock": VectorClock.from_json(parts[5])
                }
            
            return None
            
        except socket.timeout:
            sock.close()
            print("Request timeout! Trying to failover...")
            return self._failover_and_retry(command, *args)
        except Exception as e:
            sock.close()
            print(f"Request error: {e}")
            print("Trying to failover to another server...")
            return self._failover_and_retry(command, *args)
    
    def _failover_and_retry(self, command: str, *args) -> Optional[Dict]:
        """Failover to next server and retry request"""
        if len(self.servers) < 2:
            print("No backup servers available!")
            return None
        
        # Try next server
        current_idx = self.servers.index(self.current_server)
        next_idx = (current_idx + 1) % len(self.servers)
        self.current_server = self.servers[next_idx]
        
        print(f"Switched to: {self.current_server['name']}")
        
        # Retry request
        return self._send_request(command, *args)
    
    def _check_monotonic_writes(self, vc: VectorClock) -> bool:
        """Check monotonic writes guarantee"""
        if not config.MONOTONIC_WRITES:
            return True
        
        # Current write VC should be >= last write VC
        comparison = vc.compare(self.last_write_vc)
        return comparison in ['after', 'equal', 'concurrent']
    
    def _check_writes_follow_reads(self, vc: VectorClock) -> bool:
        """Check writes-follow-reads guarantee"""
        if not config.WRITES_FOLLOW_READS:
            return True
        
        # Server VC should be >= last read VC
        comparison = vc.compare(self.last_read_vc)
        return comparison in ['after', 'equal', 'concurrent']
    
    def _prefer_last_write_server(self) -> bool:
        """Route read to last write server if within TTL"""
        if not config.READ_YOUR_WRITES:
            return False
        
        if self.last_write_server is None:
            return False
        
        # Check if within cache TTL
        if time.time() - self.last_write_time > config.CLIENT_CACHE_TTL_SEC:
            return False
        
        # Switch to last write server if different
        if self.current_server['id'] != self.last_write_server:
            for server in self.servers:
                if server['id'] == self.last_write_server:
                    self.current_server = server
                    return True
        
        return True
    
    def register(self, phone: str, pin: str) -> bool:
        """Register a new account"""
        print(f"\nRegistering account {phone}...")
        
        response = self._send_request("REGISTER", phone, pin)
        
        if response and response['status'] == 'OK':
            print(f"✓ {response['message']}")
            
            # Update consistency state
            self.last_write_server = self.current_server['id']
            self.last_write_time = time.time()
            self.last_write_vc = response['vector_clock']
            
            return True
        else:
            print(f"✗ {response['message'] if response else 'Request failed'}")
            return False
    
    def check_balance(self, phone: str, pin: str) -> Optional[float]:
        """Check account balance"""
        print(f"\nChecking balance for {phone}...")
        
        # Prefer last write server for read-your-writes
        self._prefer_last_write_server()
        
        response = self._send_request("BALANCE", phone, pin)
        
        if response and response['status'] == 'OK':
            print(f"✓ Balance: UGX {response['balance']:,.2f}")
            
            # Update read vector clock
            self.last_read_vc.update(response['vector_clock'])
            
            return response['balance']
        else:
            print(f"✗ {response['message'] if response else 'Request failed'}")
            return None
    
    def deposit(self, phone: str, pin: str, amount: float) -> bool:
        """Deposit money"""
        print(f"\nDepositing UGX {amount:,.2f} to {phone}...")
        print(f"[DEBUG] Using phone: {phone}, PIN: {'*' * len(pin) if pin else 'None'}")
        
        response = self._send_request("DEPOSIT", phone, pin, amount)
        
        if response and response['status'] == 'OK':
            print(f"✓ {response['message']}")
            print(f"  New balance: UGX {response['balance']:,.2f}")
            
            # Update consistency state
            self.last_write_server = self.current_server['id']
            self.last_write_time = time.time()
            self.last_write_vc = response['vector_clock']
            
            return True
        else:
            print(f"✗ {response['message'] if response else 'Request failed'}")
            return False
    
    def withdraw(self, phone: str, pin: str, amount: float) -> bool:
        """Withdraw money"""
        print(f"\nWithdrawing UGX {amount:,.2f} from {phone}...")
        
        response = self._send_request("WITHDRAW", phone, pin, amount)
        
        if response and response['status'] == 'OK':
            print(f"✓ {response['message']}")
            print(f"  New balance: UGX {response['balance']:,.2f}")
            
            # Update consistency state
            self.last_write_server = self.current_server['id']
            self.last_write_time = time.time()
            self.last_write_vc = response['vector_clock']
            
            return True
        else:
            print(f"✗ {response['message'] if response else 'Request failed'}")
            return False
    
    def transfer(self, from_phone: str, pin: str, to_phone: str, amount: float) -> bool:
        """Transfer money to another account"""
        print(f"\nTransferring UGX {amount:,.2f} from {from_phone} to {to_phone}...")
        
        response = self._send_request("TRANSFER", from_phone, pin, to_phone, amount)
        
        if response and response['status'] == 'OK':
            print(f"✓ {response['message']}")
            print(f"  Your new balance: UGX {response['balance']:,.2f}")
            
            # Update consistency state
            self.last_write_server = self.current_server['id']
            self.last_write_time = time.time()
            self.last_write_vc = response['vector_clock']
            
            return True
        else:
            print(f"✗ {response['message'] if response else 'Request failed'}")
            return False
    
    def interactive_menu(self):
        """Interactive client menu"""
        print("\n" + "="*60)
        print("  MOBILE MONEY - Distributed System")
        print("="*60)
        
        if not self.discover_servers():
            print("\nCannot connect to any server. Please start servers first.")
            return
        
        current_phone = None
        current_pin = None
        
        while True:
            print("\n" + "-"*60)
            if current_phone:
                print(f"Logged in as: {current_phone}")
            print("-"*60)
            print("1. Register new account")
            print("2. Login")
            print("3. Check balance")
            print("4. Deposit money")
            print("5. Withdraw money")
            print("6. Transfer money")
            print("7. Switch server")
            print("8. Show server status")
            print("0. Exit")
            print("-"*60)
            
            choice = input("Select option: ").strip()
            
            if choice == '1':
                phone = input("Enter phone number: ").strip()
                pin = input("Enter 4-digit PIN: ").strip()
                
                if len(pin) != 4 or not pin.isdigit():
                    print("PIN must be 4 digits!")
                    continue
                
                if self.register(phone, pin):
                    current_phone = phone
                    current_pin = pin
            
            elif choice == '2':
                phone = input("Enter phone number: ").strip()
                pin = input("Enter PIN: ").strip()
                
                # Try to check balance to verify login
                balance = self.check_balance(phone, pin)
                if balance is not None:
                    current_phone = phone
                    current_pin = pin
                    print("✓ Login successful!")
            
            elif choice == '3':
                if not current_phone:
                    print("Please login first!")
                    continue
                
                self.check_balance(current_phone, current_pin)
            
            elif choice == '4':
                if not current_phone:
                    print("Please login first!")
                    continue
                
                try:
                    amount = float(input("Enter amount to deposit: ").strip())
                    if amount <= 0:
                        print("Amount must be positive!")
                        continue
                    
                    self.deposit(current_phone, current_pin, amount)
                except ValueError:
                    print("Invalid amount!")
            
            elif choice == '5':
                if not current_phone:
                    print("Please login first!")
                    continue
                
                try:
                    amount = float(input("Enter amount to withdraw: ").strip())
                    if amount <= 0:
                        print("Amount must be positive!")
                        continue
                    
                    self.withdraw(current_phone, current_pin, amount)
                except ValueError:
                    print("Invalid amount!")
            
            elif choice == '6':
                if not current_phone:
                    print("Please login first!")
                    continue
                
                to_phone = input("Enter recipient phone number: ").strip()
                
                if to_phone == current_phone:
                    print("Cannot transfer to yourself!")
                    continue
                
                try:
                    amount = float(input("Enter amount to transfer: ").strip())
                    if amount <= 0:
                        print("Amount must be positive!")
                        continue
                    
                    # Confirm transfer
                    print(f"\nTransfer UGX {amount:,.2f} to {to_phone}?")
                    confirm = input("Type 'yes' to confirm: ").strip().lower()
                    
                    if confirm == 'yes':
                        self.transfer(current_phone, current_pin, to_phone, amount)
                    else:
                        print("Transfer cancelled")
                except ValueError:
                    print("Invalid amount!")
            
            elif choice == '7':
                if len(self.servers) < 2:
                    print("Only one server available!")
                    continue
                
                print("\nAvailable servers:")
                for i, server in enumerate(self.servers, 1):
                    current = " (current)" if server == self.current_server else ""
                    print(f"  {i}. {server['name']} - {server['latency']:.1f}ms{current}")
                
                try:
                    idx = int(input("Select server: ").strip()) - 1
                    if 0 <= idx < len(self.servers):
                        self.current_server = self.servers[idx]
                        print(f"Switched to: {self.current_server['name']}")
                except ValueError:
                    print("Invalid selection!")
            
            elif choice == '8':
                print("\nServer Status:")
                print(f"  Current: {self.current_server['name']}")
                print(f"  Host: {self.current_server['host']}:{self.current_server['port']}")
                print(f"  Latency: {self.current_server['latency']:.1f}ms")
                print(f"\nConsistency State:")
                print(f"  Last write server: {self.last_write_server}")
                print(f"  Last write VC: {self.last_write_vc}")
                print(f"  Last read VC: {self.last_read_vc}")
            
            elif choice == '0':
                print("\nGoodbye!")
                break
            
            else:
                print("Invalid option!")


def main():
    client = MobileMoneyClient()
    
    try:
        client.interactive_menu()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")


if __name__ == "__main__":
    main()
