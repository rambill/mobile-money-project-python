#!/usr/bin/env python3
"""
Quick script to verify that config is loading correctly
"""

import json
import sys

def verify_config():
    """Verify that config.py and servers.json are correct"""
    
    print("=" * 60)
    print("CONFIG VERIFICATION")
    print("=" * 60)
    
    # Test 1: Load config.py
    print("\n1. Testing config.py...")
    try:
        import config
        print("   ✓ config.py loads successfully")
        
        print(f"\n   Found {len(config.SERVERS)} server(s):")
        for server in config.SERVERS:
            status = "ACTIVE" if server.get("active", True) else "INACTIVE"
            print(f"   - Server {server['id']}: {server['name']}")
            print(f"     Host: {server['host']}:{server['port']}")
            print(f"     Replication Port: {server['rep_port']}")
            print(f"     Status: {status}")
        
        # Check if IPs are correct
        print("\n   Checking server IPs...")
        server1 = config.get_server_by_id(1)
        server2 = config.get_server_by_id(2)
        
        if server1 and server1['host'] == "10.29.42.224":
            print("   ✓ Server 1 IP is correct: 10.29.42.224")
        else:
            print(f"   ✗ Server 1 IP is wrong: {server1['host'] if server1 else 'NOT FOUND'}")
            print("     Expected: 10.29.42.224")
        
        if server2 and server2['host'] == "10.29.42.65":
            print("   ✓ Server 2 IP is correct: 10.29.42.65")
        else:
            print(f"   ✗ Server 2 IP is wrong: {server2['host'] if server2 else 'NOT FOUND'}")
            print("     Expected: 10.29.42.65")
        
    except SyntaxError as e:
        print(f"   ✗ config.py has syntax error: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Error loading config.py: {e}")
        return False
    
    # Test 2: Load servers.json
    print("\n2. Testing servers.json...")
    try:
        with open("servers.json", "r") as f:
            data = json.load(f)
        
        print("   ✓ servers.json is valid JSON")
        
        servers = data.get("servers", [])
        print(f"\n   Found {len(servers)} server(s) in servers.json:")
        for server in servers:
            status = "ACTIVE" if server.get("active", True) else "INACTIVE"
            print(f"   - Server {server['id']}: {server.get('name', 'Unknown')}")
            print(f"     Host: {server['host']}:{server['port']}")
            print(f"     Status: {status}")
        
    except json.JSONDecodeError as e:
        print(f"   ✗ servers.json has invalid JSON: {e}")
        return False
    except FileNotFoundError:
        print("   ⚠ servers.json not found (using config.py defaults)")
    except Exception as e:
        print(f"   ✗ Error loading servers.json: {e}")
        return False
    
    # Test 3: Check replication settings
    print("\n3. Checking replication settings...")
    print(f"   - Max packet size: {config.MAX_PACKET_SIZE} bytes")
    print(f"   - UDP timeout: {config.UDP_TIMEOUT_SEC} seconds")
    print(f"   - 2PC enabled: {config.TWO_PC_ENABLED}")
    
    if config.MAX_PACKET_SIZE >= 2048:
        print("   ✓ Packet size is sufficient for vector clocks")
    else:
        print("   ⚠ Packet size might be too small")
    
    # Test 4: Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    active_servers = config.get_active_servers()
    print(f"\n✓ Configuration is valid!")
    print(f"✓ {len(active_servers)} active server(s) configured")
    print(f"\nYour servers:")
    for server in active_servers:
        print(f"  - Server {server['id']}: {server['host']}:{server['port']}")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("\n1. If databases are out of sync, follow: SYNC_DATABASES.md")
    print("2. Start servers:")
    print("   - On 10.29.42.224: python server.py 1")
    print("   - On 10.29.42.65: python server.py 2")
    print("3. Test replication with client.py")
    print("\n" + "=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = verify_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
