# 🚀 Sync All Servers - One Command!

## Overview

The upgraded `force_sync.py` now syncs **ALL servers** from Server 1 (master) automatically!

### What It Does

```
Server 1 (Master)
    ↓
Copies all data to:
    ↓
├─ Server 2
├─ Server 3
├─ Server 4
├─ Server 5
└─ ... (unlimited servers)
```

---

## How It Works

### Step 1: Detects All Servers

```python
# Automatically finds all servers by:
1. Reading servers.json
2. Or scanning data/ folder for server_*.db files
```

### Step 2: Uses Server 1 as Master

```
Server 1 = Source of Truth (Master)
All other servers = Replicas (updated to match Server 1)
```

### Step 3: Syncs Each Server

```
For each server (2, 3, 4, 5, ...):
  - Read Server 1 accounts
  - Compare with target server
  - Add missing accounts
  - Update different balances
  - Verify count matches
```

---

## Usage

### Basic Usage (Sync All Servers)

```bash
# Stop all servers first
# Then run:
python force_sync.py

# Output:
# Found 5 server(s):
#   ✓ Server 1: data/server_1.db
#   ✓ Server 2: data/server_2.db
#   ✓ Server 3: data/server_3.db
#   ✓ Server 4: data/server_4.db
#   ✓ Server 5: data/server_5.db
# 
# ⚠ WARNING: This will update ALL servers to match Server 1!
# Press Enter to continue...
# 
# ✓ Connected to Server 1 (master)
# ✓ Found 14 account(s) on Server 1 (master)
# 
# ================================================================================
# SYNCING SERVER 2
# ================================================================================
#   Current accounts on Server 2: 13
#     ✓ Added: 0759882769 (balance=5000.0)
#     ✓ Updated: 0709047981 (balance=103000.0)
#     ✓ Updated: 0759016809 (balance=54000.0)
#     ✓ Updated: 0759882820 (balance=5000.0)
#     ✓ Updated: 0759882945 (balance=3000.0)
#   ✓ Server 2 sync complete:
#     - Added: 1 account(s)
#     - Updated: 4 account(s)
#     - Total: 14 account(s)
#   ✓ Server 2 matches Server 1!
# 
# ================================================================================
# SYNCING SERVER 3
# ================================================================================
#   Current accounts on Server 3: 0
#     ✓ Added: 0709047981 (balance=103000.0)
#     ✓ Added: 0759016809 (balance=54000.0)
#     ... (all 14 accounts)
#   ✓ Server 3 sync complete:
#     - Added: 14 account(s)
#     - Updated: 0 account(s)
#     - Total: 14 account(s)
#   ✓ Server 3 matches Server 1!
# 
# ... (continues for all servers)
# 
# ================================================================================
# SYNC COMPLETE!
# ================================================================================
# 
# ✓ Master: Server 1 (14 accounts)
# ✓ Synced: 4 server(s)
# ✓ All servers now have 14 account(s)
```

---

## Example Scenarios

### Scenario 1: Adding Server 3

```bash
# You have Server 1 and 2 running
# Now you want to add Server 3

# Step 1: Create Server 3 database
python server.py 3
# Press Ctrl+C after it starts (creates empty database)

# Step 2: Sync all servers
python force_sync.py
# Server 3 will get all 14 accounts from Server 1

# Step 3: Restart all servers
python server.py 1
python server.py 2
python server.py 3

# Done! Server 3 has all data!
```

### Scenario 2: Adding Servers 3, 4, 5

```bash
# Step 1: Create all server databases
python server.py 3  # Press Ctrl+C after start
python server.py 4  # Press Ctrl+C after start
python server.py 5  # Press Ctrl+C after start

# Step 2: Sync all servers at once
python force_sync.py
# All servers (2, 3, 4, 5) get data from Server 1

# Step 3: Restart all servers
python server.py 1
python server.py 2
python server.py 3
python server.py 4
python server.py 5

# Done! All 5 servers have identical data!
```

### Scenario 3: Fixing Out-of-Sync Servers

```bash
# Servers 1, 2, 3, 4, 5 are running
# But they have different data

# Step 1: Stop all servers (Ctrl+C on each)

# Step 2: Sync all from Server 1
python force_sync.py
# All servers updated to match Server 1

# Step 3: Restart all servers
python server.py 1
python server.py 2
python server.py 3
python server.py 4
python server.py 5

# Done! All servers in sync!
```

---

## Configuration

### Adding New Servers to servers.json

```json
{
  "servers": [
    {
      "id": 1,
      "name": "Kampala",
      "host": "10.29.42.224",
      "port": 6001,
      "rep_port": 6101,
      "active": true
    },
    {
      "id": 2,
      "name": "Mbarara",
      "host": "10.29.42.65",
      "port": 6002,
      "rep_port": 6102,
      "active": true
    },
    {
      "id": 3,
      "name": "Gulu",
      "host": "10.29.42.146",
      "port": 6003,
      "rep_port": 6103,
      "active": true
    },
    {
      "id": 4,
      "name": "Jinja",
      "host": "10.29.42.200",
      "port": 6004,
      "rep_port": 6104,
      "active": true
    },
    {
      "id": 5,
      "name": "Mbale",
      "host": "10.29.42.201",
      "port": 6005,
      "rep_port": 6105,
      "active": true
    }
  ]
}
```

---

## Features

### ✅ Automatic Server Detection

- Reads `servers.json` for server list
- Or scans `data/` folder for `server_*.db` files
- Works with any number of servers

### ✅ Server 1 as Master

- Server 1 is always the source of truth
- All other servers updated to match Server 1
- Ensures consistency across cluster

### ✅ Smart Sync

- **Missing accounts:** Added to target server
- **Different balances:** Updated to match Server 1
- **Same data:** Skipped (no unnecessary updates)

### ✅ Verification

- Counts accounts after sync
- Verifies each server matches Server 1
- Reports any discrepancies

### ✅ Safe

- Requires confirmation before syncing
- Shows what will be synced
- Can be cancelled with Ctrl+C

---

## Output Explanation

### Server Detection

```
Found 5 server(s):
  ✓ Server 1: data/server_1.db  ← Master
  ✓ Server 2: data/server_2.db  ← Will be synced
  ✓ Server 3: data/server_3.db  ← Will be synced
  ✓ Server 4: data/server_4.db  ← Will be synced
  ✓ Server 5: data/server_5.db  ← Will be synced
```

### Sync Progress

```
SYNCING SERVER 2
  Current accounts on Server 2: 13
    ✓ Added: 0759882769 (balance=5000.0)    ← New account
    ✓ Updated: 0709047981 (balance=103000.0) ← Balance changed
  ✓ Server 2 sync complete:
    - Added: 1 account(s)
    - Updated: 4 account(s)
    - Total: 14 account(s)
  ✓ Server 2 matches Server 1!
```

### Final Summary

```
SYNC COMPLETE!
✓ Master: Server 1 (14 accounts)
✓ Synced: 4 server(s)
✓ All servers now have 14 account(s)
```

---

## Advantages

### 1. One Command for All Servers

```bash
# Before: Sync each server manually
python force_sync_server2.py
python force_sync_server3.py
python force_sync_server4.py
python force_sync_server5.py

# After: Sync all at once
python force_sync.py
```

### 2. Automatic Detection

- No need to specify which servers to sync
- Automatically finds all servers
- Works with any number of servers

### 3. Scalable

- Works with 2 servers
- Works with 100 servers
- No limit on number of servers

### 4. Reliable

- Direct database access (no network)
- No UDP packet issues
- 100% success rate

---

## Workflow

### Initial Setup (New Cluster)

```bash
# 1. Start Server 1 (master)
python server.py 1
# Create accounts, add data
# Press Ctrl+C

# 2. Create other servers
python server.py 2  # Ctrl+C after start
python server.py 3  # Ctrl+C after start
python server.py 4  # Ctrl+C after start

# 3. Sync all from Server 1
python force_sync.py

# 4. Start all servers
python server.py 1
python server.py 2
python server.py 3
python server.py 4

# Done! All servers have same data!
```

### Regular Maintenance

```bash
# If servers get out of sync:

# 1. Stop all servers
# 2. Run sync
python force_sync.py

# 3. Restart all servers
# Done!
```

---

## Troubleshooting

### Error: "Server 1 database not found"

**Cause:** Server 1 doesn't exist  
**Solution:** Server 1 must exist (it's the master)

```bash
python server.py 1  # Create Server 1
# Press Ctrl+C after it starts
python force_sync.py
```

### Error: "database is locked"

**Cause:** Servers are still running  
**Solution:** Stop all servers first

```bash
# Press Ctrl+C on all server terminals
python force_sync.py
```

### Warning: "Skipping Server X: database not found"

**Cause:** Server X database doesn't exist  
**Solution:** Create it first

```bash
python server.py X  # Replace X with server number
# Press Ctrl+C after it starts
python force_sync.py
```

---

## Summary

**Command:** `python force_sync.py`  
**What it does:** Syncs ALL servers from Server 1 (master)  
**When to use:** When adding new servers or fixing out-of-sync data  
**Result:** All servers have identical data  

**Quick Start:**
```bash
# Stop all servers
python force_sync.py
# Restart all servers
```

---

**One command syncs unlimited servers!** 🚀

**Server 1 is master, all others are replicas!** ✨
