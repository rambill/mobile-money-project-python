#!/usr/bin/env python3
"""
Simple test without broadcast (Windows-friendly)
"""

import socket
import time

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
    except Exception as e:
        sock.close()
        print(f"   Error: {e}")
        return None

print("\n" + "="*60)
print("  SIMPLE MOBILE MONEY TEST")
print("="*60)

# Test phone and PIN
phone = f"0759{int(time.time()) % 1000000}"
pin = "1234"

print(f"\nTest Account: {phone}, PIN: {pin}")
print("-"*60)

# Test 1: Register
print("\n1. REGISTER on Server 1...")
response = send_request("127.0.0.1", 6001, "REGISTER", phone, pin)
if response and "OK" in response:
    print("   ✓ SUCCESS - Account registered")
else:
    print(f"   ✗ FAILED - {response}")
    exit(1)

# Wait for replication
print("\n2. Waiting 1 second for replication...")
time.sleep(1)

# Test 2: Check balance on Server 2
print("\n3. BALANCE on Server 2 (testing replication)...")
response = send_request("127.0.0.1", 6002, "BALANCE", phone, pin)
if response and "OK" in response:
    print("   ✓ SUCCESS - Account replicated to Server 2")
else:
    print(f"   ✗ FAILED - {response}")
    print("   (Replication may not be working)")

# Test 3: Deposit
print("\n4. DEPOSIT 5000 on Server 1...")
response = send_request("127.0.0.1", 6001, "DEPOSIT", phone, pin, 5000)
print(f"   Response: {response}")

if response and "OK" in response:
    parts = response.split('|')
    balance = parts[4] if len(parts) > 4 else "?"
    print(f"   ✓ SUCCESS - Deposit complete, balance: {balance}")
else:
    print(f"   ✗ FAILED - Deposit did not complete")
    if response is None:
        print("   (Timeout - server may be stuck)")
    exit(1)

# Wait for replication
print("\n5. Waiting 1 second for replication...")
time.sleep(1)

# Test 4: Check balance on Server 3
print("\n6. BALANCE on Server 3 (testing deposit replication)...")
response = send_request("127.0.0.1", 6003, "BALANCE", phone, pin)
if response and "OK" in response:
    parts = response.split('|')
    balance = parts[4] if len(parts) > 4 else "?"
    print(f"   ✓ SUCCESS - Balance on Server 3: {balance}")
    
    if balance == "5000.0":
        print("\n" + "="*60)
        print("  🎉 ALL TESTS PASSED!")
        print("="*60)
        print("\n  Your mobile money system is working perfectly!")
        print("  You can now use: python client.py")
    else:
        print(f"\n   ⚠️  Balance mismatch - expected 5000.0, got {balance}")
else:
    print(f"   ✗ FAILED - {response}")

print("\n" + "="*60)
