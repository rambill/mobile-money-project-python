#!/usr/bin/env python3
"""
Test concurrent client operations
This simulates multiple clients performing operations simultaneously
"""

import socket
import time
import threading

def send_request(host, port, command, *args):
    """Send a request to server"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5.0)
    
    req_id = f"test_{threading.current_thread().name}_{int(time.time() * 1000000)}"
    message = f"REQ|{req_id}|{command}|" + "|".join(str(arg) for arg in args)
    
    try:
        sock.sendto(message.encode(), (host, port))
        data, _ = sock.recvfrom(2048)
        response = data.decode().strip()
        sock.close()
        return response
    except Exception as e:
        sock.close()
        return None

def concurrent_deposit(phone, pin, amount, thread_id):
    """Perform a deposit from a thread"""
    response = send_request("127.0.0.1", 6001, "DEPOSIT", phone, pin, amount)
    if response and "OK" in response:
        parts = response.split('|')
        balance = parts[4] if len(parts) > 4 else "?"
        print(f"  Thread {thread_id}: Deposited {amount}, balance: {balance}")
        return True
    else:
        print(f"  Thread {thread_id}: Failed - {response}")
        return False

print("\n" + "="*60)
print("  CONCURRENCY TEST")
print("="*60)

# Create test account
phone = f"0759{int(time.time()) % 1000000}"
pin = "1234"

print(f"\nTest Account: {phone}, PIN: {pin}")
print("-"*60)

# Register account
print("\n1. Registering account...")
response = send_request("127.0.0.1", 6001, "REGISTER", phone, pin)
if response and "OK" in response:
    print("   ✓ Account registered")
else:
    print(f"   ✗ Failed: {response}")
    exit(1)

# Test 1: Concurrent deposits
print("\n2. Testing 5 concurrent deposits of 1000 each...")
print("   (Should result in balance of 5000)")

threads = []
for i in range(5):
    t = threading.Thread(target=concurrent_deposit, args=(phone, pin, 1000, i+1))
    threads.append(t)
    t.start()

# Wait for all threads to complete
for t in threads:
    t.join()

# Wait for replication
time.sleep(1)

# Check final balance
print("\n3. Checking final balance...")
response = send_request("127.0.0.1", 6001, "BALANCE", phone, pin)
if response and "OK" in response:
    parts = response.split('|')
    balance = float(parts[4]) if len(parts) > 4 else 0
    print(f"   Final balance: {balance}")
    
    if balance == 5000.0:
        print("   ✓ CORRECT! All 5 deposits were processed correctly")
        print("   ✓ No race conditions detected")
    else:
        print(f"   ✗ INCORRECT! Expected 5000.0, got {balance}")
        print("   ✗ Race condition detected - some deposits were lost")
else:
    print(f"   ✗ Failed to check balance: {response}")

# Test 2: Concurrent withdrawals
print("\n4. Testing 3 concurrent withdrawals of 500 each...")
print("   (Should result in balance of 3500)")

def concurrent_withdraw(phone, pin, amount, thread_id):
    """Perform a withdrawal from a thread"""
    response = send_request("127.0.0.1", 6001, "WITHDRAW", phone, pin, amount)
    if response and "OK" in response:
        parts = response.split('|')
        balance = parts[4] if len(parts) > 4 else "?"
        print(f"  Thread {thread_id}: Withdrew {amount}, balance: {balance}")
        return True
    else:
        print(f"  Thread {thread_id}: Failed - {response}")
        return False

threads = []
for i in range(3):
    t = threading.Thread(target=concurrent_withdraw, args=(phone, pin, 500, i+1))
    threads.append(t)
    t.start()

# Wait for all threads to complete
for t in threads:
    t.join()

# Wait for replication
time.sleep(1)

# Check final balance
print("\n5. Checking final balance...")
response = send_request("127.0.0.1", 6001, "BALANCE", phone, pin)
if response and "OK" in response:
    parts = response.split('|')
    balance = float(parts[4]) if len(parts) > 4 else 0
    print(f"   Final balance: {balance}")
    
    if balance == 3500.0:
        print("   ✓ CORRECT! All 3 withdrawals were processed correctly")
        print("   ✓ No race conditions detected")
    else:
        print(f"   ✗ INCORRECT! Expected 3500.0, got {balance}")
        print("   ✗ Race condition detected")
else:
    print(f"   ✗ Failed to check balance: {response}")

print("\n" + "="*60)
print("  CONCURRENCY TEST COMPLETE!")
print("="*60)

if balance == 3500.0:
    print("\n✓ All concurrent operations handled correctly!")
    print("✓ Thread-safe atomic operations working!")
    print("✓ No race conditions detected!")
    print("\nYour system can handle multiple clients safely!")
else:
    print("\n⚠️  Some operations were not processed correctly")
    print("   This indicates a race condition issue")
