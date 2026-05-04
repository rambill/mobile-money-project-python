#!/usr/bin/env python3
"""
Diagnostic script to check server health
"""

import socket
import time
import json

def check_server(server_id, host, port):
    """Check if a server is responding"""
    print(f"\nChecking Server {server_id} ({host}:{port})...")
    
    # Try discovery
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        sock.sendto(b"DISCOVER", ('<broadcast>', 5999))
        
        start = time.time()
        while time.time() - start < 2.0:
            try:
                data, addr = sock.recvfrom(512)
                info = json.loads(data.decode())
                if info['id'] == server_id:
                    print(f"  ✓ Server {server_id} responding to discovery")
                    print(f"    Name: {info['name']}")
                    print(f"    Load: {info['load']} requests")
                    break
            except socket.timeout:
                break
        sock.close()
    except Exception as e:
        print(f"  ✗ Discovery failed: {e}")
    
    # Try direct RPC
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        
        # Try a simple balance check with fake account
        message = f"REQ|diag_{time.time()}|BALANCE|test|0000"
        sock.sendto(message.encode(), (host, port))
        
        data, _ = sock.recvfrom(512)
        response = data.decode()
        
        if "RES" in response:
            print(f"  ✓ Server {server_id} responding to RPC")
            print(f"    Response: {response[:50]}...")
        else:
            print(f"  ✗ Unexpected response: {response}")
        
        sock.close()
    except socket.timeout:
        print(f"  ✗ RPC timeout - server not responding")
    except Exception as e:
        print(f"  ✗ RPC failed: {e}")

print("="*60)
print("DIAGNOSTIC CHECK")
print("="*60)

# Check all 3 servers
check_server(1, "127.0.0.1", 6001)
check_server(2, "127.0.0.1", 6002)
check_server(3, "127.0.0.1", 6003)

print("\n" + "="*60)
print("RECOMMENDATION")
print("="*60)

print("""
If any server shows ✗:
1. Make sure the server is running: python server.py <id>
2. Check for errors in the server terminal
3. Try restarting the server

If all servers show ✓:
1. The servers are healthy
2. Try running: python quick_test.py
3. If still failing, check server logs for errors
""")
