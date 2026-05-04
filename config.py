# Configuration for Distributed Mobile Money System

import json
import os

# Server Configuration
SERVERS = [
    {
        "id": 1,
        "name": "MoMo-Kampala",
        "region": "Central Uganda",
        "host": "10.29.42.224",
        "port": 6001,
        "rep_port": 6101,
        "active": True,
    },
    {
        "id": 2,
        "name": "MoMo-Mbarara",
        "region": "Western Uganda",
        "host": "10.29.42.65",
        "port": 6002,
        "rep_port": 6102,
        "active": True,
    },
    {
        "id": 3,
        "name": "MoMo-Gulu",
        "region": "Northern Uganda",
        "host": "10.29.42.17",
        "port": 6003,
        "rep_port": 6103,
        "active": True,
    },
]

# Load servers from servers.json if it exists
if os.path.exists("servers.json"):
    try:
        with open("servers.json", "r") as f:
            data = json.load(f)
            SERVERS = data.get("servers", SERVERS)
    except Exception as e:
        print(f"Warning: Could not load servers.json: {e}")

# Network Configuration
DISCOVERY_PORT = 5999
MAX_PACKET_SIZE = 65507  # Maximum UDP packet size (protocol limit)
UDP_TIMEOUT_SEC = 10.0  # Increased timeout for large state transfers
CHUNK_SIZE = 60000  # Size of each chunk for large data transfers (leave room for headers)

# Election Configuration (Bully Algorithm)
ELECTION_TIMEOUT_SEC = 3.0
COORDINATOR_HEARTBEAT_SEC = 5.0
COORDINATOR_TIMEOUT_SEC = 12.0

# Clock Synchronization (Berkeley Algorithm)
CLOCK_SYNC_INTERVAL_SEC = 15.0
MAX_CLOCK_DRIFT_SEC = 5.0

# Distributed Locks
LOCK_TIMEOUT_SEC = 5.0
LOCK_REQUEST_TIMEOUT_SEC = 3.0

# Two-Phase Commit
TWO_PC_ENABLED = False  # Temporarily disabled for stability
TWO_PC_TIMEOUT_SEC = 3.0
TWO_PC_WAL_DIR = "wal"

# Conflict Resolution
CONFLICT_STRATEGY = "LWW"  # Last-Writer-Wins

# Anti-Entropy / Gossip
GOSSIP_INTERVAL_SEC = 60.0
MERKLE_HASH_DEPTH = 4

# Caching
CLIENT_CACHE_TTL_SEC = 5.0
SERVER_CACHE_TTL_SEC = 10.0

# Client-Centric Consistency Models
READ_YOUR_WRITES = True
MONOTONIC_READS = True
MONOTONIC_WRITES = True
WRITES_FOLLOW_READS = True

# Database Configuration
DB_DIR = "data"
DB_NAME_TEMPLATE = "server_{}.db"

# Replication
REPLICATION_LOG_SIZE = 1000
STATE_SYNC_ON_STARTUP = True  # Automatically sync state from peers on startup if database is empty

# Heartbeat & Failure Detection
HEARTBEAT_INTERVAL_SEC = 3.0
FAILURE_DETECTION_TIMEOUT_SEC = 10.0

def get_server_by_id(server_id):
    """Get server configuration by ID"""
    for server in SERVERS:
        if server["id"] == server_id:
            return server
    return None

def get_active_servers():
    """Get list of active servers"""
    return [s for s in SERVERS if s.get("active", True)]
