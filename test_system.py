#!/usr/bin/env python3
"""
Comprehensive System Test
Tests all distributed systems features
"""

import time
import sys
from distributed import VectorClock, ConflictResolver, MerkleTree


def test_vector_clocks():
    """Test vector clock operations"""
    print("\n" + "="*60)
    print("TEST: Vector Clocks")
    print("="*60)
    
    # Create vector clocks
    vc1 = VectorClock()
    vc1.increment(1)
    vc1.increment(1)
    
    vc2 = VectorClock()
    vc2.increment(2)
    
    vc3 = VectorClock()
    vc3.increment(1)
    vc3.increment(2)
    
    # Test comparisons
    assert vc1.compare(vc2) == 'concurrent', "VC1 and VC2 should be concurrent"
    assert vc1.compare(vc3) == 'before', "VC1 should be before VC3"
    assert vc3.compare(vc1) == 'after', "VC3 should be after VC1"
    
    # Test serialization
    json_str = vc1.to_json()
    vc1_restored = VectorClock.from_json(json_str)
    assert vc1.clock == vc1_restored.clock, "Serialization should preserve clock"
    
    print("✓ Vector clock increment")
    print("✓ Vector clock comparison (before/after/concurrent)")
    print("✓ Vector clock serialization")
    print("\nVector Clocks: PASSED")


def test_conflict_resolution():
    """Test Last-Writer-Wins conflict resolution"""
    print("\n" + "="*60)
    print("TEST: Conflict Resolution (LWW)")
    print("="*60)
    
    # Create concurrent states
    vc1 = VectorClock({1: 2, 2: 1})
    vc2 = VectorClock({1: 1, 2: 2})
    
    state1 = {
        'data': 'value1',
        'vector_clock': vc1,
        'physical_timestamp': 1000.0,
        'server_id': 1
    }
    
    state2 = {
        'data': 'value2',
        'vector_clock': vc2,
        'physical_timestamp': 1001.0,  # Later timestamp
        'server_id': 2
    }
    
    # Resolve conflict
    winner = ConflictResolver.resolve(state1, state2)
    
    assert winner == state2, "Later timestamp should win"
    
    # Test with same timestamp
    state2['physical_timestamp'] = 1000.0
    winner = ConflictResolver.resolve(state1, state2)
    
    assert winner['server_id'] == 2, "Higher server ID should win on tie"
    
    print("✓ LWW with physical timestamp")
    print("✓ LWW with server ID tiebreaker")
    print("\nConflict Resolution: PASSED")


def test_merkle_tree():
    """Test Merkle tree for anti-entropy"""
    print("\n" + "="*60)
    print("TEST: Merkle Tree")
    print("="*60)
    
    merkle = MerkleTree(depth=4)
    
    # Create test data
    data1 = {
        'account1': 'hash1',
        'account2': 'hash2',
        'account3': 'hash3'
    }
    
    data2 = {
        'account1': 'hash1',
        'account2': 'hash2_modified',  # Different
        'account3': 'hash3'
    }
    
    # Build trees
    root1 = merkle.build(data1)
    root2 = merkle.build(data2)
    
    assert root1 != root2, "Different data should produce different roots"
    
    # Same data should produce same root
    root1_again = merkle.build(data1)
    assert root1 == root1_again, "Same data should produce same root"
    
    print("✓ Merkle tree construction")
    print("✓ Merkle root comparison")
    print("✓ Deterministic hashing")
    print("\nMerkle Tree: PASSED")


def test_database_schema():
    """Test database schema"""
    print("\n" + "="*60)
    print("TEST: Database Schema")
    print("="*60)
    
    import sqlite3
    import os
    
    # Create test database
    test_db = "test_schema.db"
    
    try:
        conn = sqlite3.connect(test_db)
        
        # Load schema
        with open('mobile.sql', 'r') as f:
            schema = f.read()
        
        conn.executescript(schema)
        
        # Verify tables exist
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['accounts', 'transactions', 'replication_log', 
                          'server_registry', 'cache', 'wal_2pc']
        
        for table in required_tables:
            assert table in tables, f"Table {table} should exist"
        
        # Test insert
        conn.execute(
            "INSERT INTO accounts (phone, pin, balance, vector_clock) VALUES (?, ?, ?, ?)",
            ('256700123456', '1234', 1000.0, '{}')
        )
        conn.commit()
        
        # Test query
        cursor = conn.execute("SELECT * FROM accounts WHERE phone = ?", ('256700123456',))
        row = cursor.fetchone()
        
        assert row is not None, "Should retrieve inserted account"
        
        conn.close()
        
        print("✓ Schema creation")
        print("✓ All required tables present")
        print("✓ Insert and query operations")
        print("\nDatabase Schema: PASSED")
        
    finally:
        if os.path.exists(test_db):
            os.remove(test_db)


def test_config():
    """Test configuration"""
    print("\n" + "="*60)
    print("TEST: Configuration")
    print("="*60)
    
    import config
    
    # Test server configuration
    assert len(config.SERVERS) >= 3, "Should have at least 3 servers configured"
    
    # Test get_server_by_id
    server1 = config.get_server_by_id(1)
    assert server1 is not None, "Should find server 1"
    assert server1['id'] == 1, "Server ID should match"
    
    # Test get_active_servers
    active = config.get_active_servers()
    assert len(active) > 0, "Should have active servers"
    
    # Test configuration values
    assert config.TWO_PC_ENABLED == True, "2PC should be enabled"
    assert config.CONFLICT_STRATEGY == "LWW", "Should use LWW strategy"
    
    print("✓ Server configuration loaded")
    print("✓ Helper functions work")
    print("✓ Feature flags set correctly")
    print("\nConfiguration: PASSED")


def test_protocol():
    """Test RPC protocol format"""
    print("\n" + "="*60)
    print("TEST: RPC Protocol")
    print("="*60)
    
    # Test request format
    request = "REQ|12345|DEPOSIT|256700123456|1234|5000"
    parts = request.split('|')
    
    assert parts[0] == "REQ", "Should be request"
    assert parts[1] == "12345", "Should have request ID"
    assert parts[2] == "DEPOSIT", "Should have command"
    assert len(parts) == 6, "Should have all parameters"
    
    # Test response format
    response = "RES|12345|OK|Success|15000.0|{}"
    parts = response.split('|')
    
    assert parts[0] == "RES", "Should be response"
    assert parts[2] == "OK", "Should have status"
    assert float(parts[4]) == 15000.0, "Should have balance"
    
    # Test packet size
    import config
    assert len(request.encode()) <= config.MAX_PACKET_SIZE, "Request should fit in packet"
    assert len(response.encode()) <= config.MAX_PACKET_SIZE, "Response should fit in packet"
    
    print("✓ Request format")
    print("✓ Response format")
    print("✓ Packet size constraints")
    print("\nRPC Protocol: PASSED")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("  DISTRIBUTED MOBILE MONEY - SYSTEM TESTS")
    print("="*60)
    
    tests = [
        ("Vector Clocks", test_vector_clocks),
        ("Conflict Resolution", test_conflict_resolution),
        ("Merkle Tree", test_merkle_tree),
        ("Database Schema", test_database_schema),
        ("Configuration", test_config),
        ("RPC Protocol", test_protocol),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ {name}: FAILED")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ {name}: ERROR")
            print(f"  Error: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"  TEST RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("\n✓ All tests passed! System is ready to use.")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
