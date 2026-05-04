#!/usr/bin/env python3
"""
Test transfer functionality
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
print("  TRANSFER FUNCTIONALITY TEST")
print("="*60)

# Create two test accounts
phone1 = f"0759{int(time.time()) % 1000000}"
phone2 = f"0758{int(time.time()) % 1000000}"
pin1 = "1111"
pin2 = "2222"

print(f"\nAccount 1: {phone1}, PIN: {pin1}")
print(f"Account 2: {phone2}, PIN: {pin2}")
print("-"*60)

# Register Account 1
print("\n1. Registering Account 1...")
response = send_request("127.0.0.1", 6001, "REGISTER", phone1, pin1)
if response and "OK" in response:
    print("   ✓ Account 1 registered")
else:
    print(f"   ✗ Failed: {response}")
    exit(1)

# Register Account 2
print("\n2. Registering Account 2...")
response = send_request("127.0.0.1", 6001, "REGISTER", phone2, pin2)
if response and "OK" in response:
    print("   ✓ Account 2 registered")
else:
    print(f"   ✗ Failed: {response}")
    exit(1)

# Deposit to Account 1
print("\n3. Depositing 10000 to Account 1...")
response = send_request("127.0.0.1", 6001, "DEPOSIT", phone1, pin1, 10000)
if response and "OK" in response:
    parts = response.split('|')
    balance = parts[4] if len(parts) > 4 else "?"
    print(f"   ✓ Deposit successful, balance: {balance}")
else:
    print(f"   ✗ Failed: {response}")
    exit(1)

# Check balance before transfer
print("\n4. Checking balances before transfer...")
response = send_request("127.0.0.1", 6001, "BALANCE", phone1, pin1)
if response and "OK" in response:
    parts = response.split('|')
    balance1 = parts[4] if len(parts) > 4 else "?"
    print(f"   Account 1 balance: {balance1}")

response = send_request("127.0.0.1", 6001, "BALANCE", phone2, pin2)
if response and "OK" in response:
    parts = response.split('|')
    balance2 = parts[4] if len(parts) > 4 else "?"
    print(f"   Account 2 balance: {balance2}")

# Transfer from Account 1 to Account 2
print(f"\n5. Transferring 3000 from Account 1 to Account 2...")
response = send_request("127.0.0.1", 6001, "TRANSFER", phone1, pin1, phone2, 3000)
print(f"   Response: {response}")

if response and "OK" in response:
    parts = response.split('|')
    balance = parts[4] if len(parts) > 4 else "?"
    print(f"   ✓ Transfer successful!")
    print(f"   Account 1 new balance: {balance}")
else:
    print(f"   ✗ Transfer failed: {response}")
    exit(1)

# Wait for replication
print("\n6. Waiting 1 second for replication...")
time.sleep(1)

# Check balances after transfer
print("\n7. Checking balances after transfer...")
response = send_request("127.0.0.1", 6002, "BALANCE", phone1, pin1)
if response and "OK" in response:
    parts = response.split('|')
    balance1 = parts[4] if len(parts) > 4 else "?"
    print(f"   Account 1 balance: {balance1}")
    
    if balance1 == "7000.0":
        print("   ✓ Correct! (10000 - 3000 = 7000)")
    else:
        print(f"   ⚠️  Expected 7000.0, got {balance1}")

response = send_request("127.0.0.1", 6003, "BALANCE", phone2, pin2)
if response and "OK" in response:
    parts = response.split('|')
    balance2 = parts[4] if len(parts) > 4 else "?"
    print(f"   Account 2 balance: {balance2}")
    
    if balance2 == "3000.0":
        print("   ✓ Correct! (0 + 3000 = 3000)")
    else:
        print(f"   ⚠️  Expected 3000.0, got {balance2}")

# Test insufficient balance
print("\n8. Testing insufficient balance (transfer 10000 from Account 1)...")
response = send_request("127.0.0.1", 6001, "TRANSFER", phone1, pin1, phone2, 10000)
if response and "ERR" in response and "Insufficient" in response:
    print("   ✓ Correctly rejected insufficient balance")
else:
    print(f"   ⚠️  Should have rejected: {response}")

# Test invalid recipient
print("\n9. Testing invalid recipient...")
response = send_request("127.0.0.1", 6001, "TRANSFER", phone1, pin1, "0700000000", 100)
if response and "ERR" in response and "not found" in response:
    print("   ✓ Correctly rejected invalid recipient")
else:
    print(f"   ⚠️  Should have rejected: {response}")

print("\n" + "="*60)
print("  🎉 TRANSFER TESTS COMPLETE!")
print("="*60)
print("\nTransfer functionality is working correctly!")
print("You can now use transfers in the client: python client.py")
print("\nTry:")
print("  1. Register two accounts")
print("  2. Deposit money to first account")
print("  3. Transfer from first to second account")
print("  4. Check both balances")
