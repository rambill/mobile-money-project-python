#!/usr/bin/env python3
"""
Quick test to verify the system works
"""

import socket
import time
import json

def send_request(host, port, command, *args):
    """Send a request to server"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5.0)
    
    req_id = f"test_{int(time.time() * 1000)}"
    message = f"REQ|{req_id}|{command}|" + "|".join(str(arg) for arg in args)
    
    try:
        sock.sendto(message.encode(), (host, port))
        data, _ = sock.recvfrom(512)
        response = data.decode().strip()
        sock.close()
        return response
    except socket.timeout:
        sock.close()
        return None

print("Testing Mobile Money System...")
print("="*60)

# Test phone and PIN
phone = f"256700{int(time.time()) % 1000000}"
pin = "1234"

print(f"\n1. Testing REGISTER on Server 1...")
response = send_request("127.0.0.1", 6001, "REGISTER", phone, pin)
if response and "OK" in response:
    print(f"   ✓ Account registered: {phone}")
else:
    print(f"   ✗ Registration failed: {response}")
    exit(1)

# Wait for replication
print("\n2. Waiting 2 seconds for replication...")
time.sleep(2)

print("\n3. Testing BALANCE on Server 2 (should be replicated)...")
response = send_request("127.0.0.1", 6002, "BALANCE", phone, pin)
if response and "OK" in response:
    print(f"   ✓ Account found on Server 2 (replication works!)")
else:
    print(f"   ✗ Account not found on Server 2: {response}")

print("\n4. Testing DEPOSIT on Server 1...")
response = send_request("127.0.0.1", 6001, "DEPOSIT", phone, pin, 5000)
print(f"   Response: {response}")
if response and "OK" in response:
    parts = response.split('|')
    balance = parts[4] if len(parts) > 4 else "?"
    print(f"   ✓ Deposit successful, balance: {balance}")
else:
    print(f"   ✗ Deposit failed: {response}")
    if response is None:
        print(f"   (Server timeout - check if server 1 is running)")
        print(f"   Try running: python admin.py status")

# Wait for replication
print("\n5. Waiting 2 seconds for replication...")
time.sleep(2)

print("\n6. Testing BALANCE on Server 3 (should show deposit)...")
response = send_request("127.0.0.1", 6003, "BALANCE", phone, pin)
if response and "OK" in response:
    parts = response.split('|')
    balance = parts[4] if len(parts) > 4 else "?"
    print(f"   ✓ Balance on Server 3: {balance}")
else:
    print(f"   ✗ Balance check failed: {response}")

print("\n" + "="*60)
print("Test complete!")
print("\nIf all tests passed, the system is working correctly.")
print("You can now use: python client.py")
