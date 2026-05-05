# 🌐 Network Sync - Sync Servers Across Different Machines

## Overview

**`network_sync.py`** is a network-based synchronization tool that syncs servers **across different machines** using UDP communication.

Unlike `peer_sync.py` (which only works on local databases), `network_sync.py` connects to servers via network and works even when servers are on different physical machines!

---

## 🎯 When to Use

### Use `network_sync.py` when:
- ✅ Servers are on **different machines**
- ✅ You want to sync **without stopping servers**
- ✅ You want to add a **new server on a different machine**
- ✅ Servers are **already running**

### Use `peer_sync.py` when:
- ✅ All servers are on the **same machine**
- ✅ Servers are **stopped**
- ✅ You have **direct access to database files**

---

## 🚀 Quick Start

### Step 1: Make Sure All Servers Are Running

```bash
# On Machine 1:
python server.py 1   # Kampala

# On Machine 2:
python server.py 10  # Arua

# On Machine 3:
python server.py 5   # Kabale

# ... etc
```

### Step 2: Run Network Sync (From Any Machine)

```bash
# Can run from any machine that has network access to all servers:
python network_sync.py

# Output:
# ============================================================
# NETWORK PEER-TO-PEER SYNC - SYNC ACROSS DIFFERENT MACHINES
# ============================================================
# 
# Found 10 active server(s) in config:
#   Server 1: Kampala (10.29.42.224:6001)
#   Server 2: Mbarara (10.29.42.65:6002)
#   ...
#   Server 10: Arua (10.29.42.56:6010)
# 
# Press Enter to continue...
```

### Step 3: Wait for Sync to Complete

```bash
# The tool will:
# 1. Collect data from all running servers
# 2. Merge data using Last-Writer-Wins
# 3. Send merged data back to all servers
# 
# ✓ All servers now have identical data!
```

**That's it! No server restart needed!** 🎉

---

## 📋 How It Works

### Step 1: Data Collection

```
network_sync.py → Server 1 (Machine 1): "Give me all your accounts"
                ← Server 1: {account1, account2, ...}

network_sync.py → Server 10 (Machine 2): "Give me all your accounts"
                ← Server 10: {account5, account6, ...}

network_sync.py → Server 5 (Machine 3): "Give me all your accounts"
                ← Server 5: {account3, account4, ...}
```

### Step 2: Data Merging

```
All accounts collected:
- account1 (from Server 1, timestamp: 100)
- account2 (from Server 1, timestamp: 200)
- account3 (from Server 5, timestamp: 150)
- account4 (from Server 5, timestamp: 250)
- account5 (from Server 10, timestamp: 180)
- account6 (from Server 10, timestamp: 220)

Conflicts resolved using Last-Writer-Wins (newest timestamp)
```

### Step 3: Data Distribution

```
network_sync.py → Server 1: "Here are all accounts you're missing"
network_sync.py → Server 10: "Here are all accounts you're missing"
network_sync.py → Server 5: "Here are all accounts you're missing"

✓ All servers now have all 6 accounts!
```

---

## 🎯 Example Scenario

### Scenario: Adding Server 10 on a New Machine

**Initial State:**
- Machine 1: Server 1 (Kampala) - has 14 accounts
- Machine 2: Server 2 (Mbarara) - has 14 accounts
- Machine 3: Server 10 (Arua) - **NEW, empty database**

**Goal:** Server 10 should get all 14 accounts

### Solution:

```bash
# Step 1: Start Server 10 on Machine 3
# On Machine 3:
python server.py 10

# Server 10 starts with empty database

# Step 2: Run network sync (from any machine)
# On Machine 1 (or any machine):
python network_sync.py

# Output:
# STEP 1: COLLECTING DATA FROM ALL SERVERS
# Server 1: Kampala
#   Requesting state from Kampala (10.29.42.224:6101)...
#   ✓ Received 14 account(s) from Kampala
#     0759016809 (balance=54000.0) [NEW]
#     0759882820 (balance=5000.0) [NEW]
#     ... (12 more accounts)
# 
# Server 10: Arua
#   Requesting state from Arua (10.29.42.56:6110)...
#   ✓ Received 0 account(s) from Arua
# 
# ✓ Total unique accounts collected: 14
# 
# STEP 2: DISTRIBUTING MERGED DATA TO ALL SERVERS
# SYNCING SERVER 10: Arua
#   Current accounts: 0
#     ✓ Added: 0759016809 (balance=54000.0) [from Server 1]
#     ✓ Added: 0759882820 (balance=5000.0) [from Server 1]
#     ... (12 more)
#   ✓ Server 10 sync complete:
#     - Added: 14 account(s)
#     - Updated: 0 account(s)
#     - Expected total: 14 account(s)
# 
# ✓ All servers now have 14 account(s)!
```

**Result:** Server 10 now has all 14 accounts! ✅

---

## 🔧 Configuration

### Update servers.json

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
      "id": 10,
      "name": "Arua",
      "host": "10.29.42.56",
      "port": 6010,
      "rep_port": 6110,
      "active": true
    }
  ]
}
```

### Update config.py

```python
SERVERS = [
    {
        "id": 1,
        "name": "Kampala",
        "host": "10.29.42.224",
        "port": 6001,
        "rep_port": 6101,
        "active": True,
    },
    {
        "id": 10,
        "name": "Arua",
        "host": "10.29.42.56",
        "port": 6010,
        "rep_port": 6110,
        "active": True,
    },
]
```

---

## 🌐 Network Requirements

### Firewall Rules

**On each server machine, allow UDP ports:**

```powershell
# Windows:
# Allow replication ports (6101-6110):
New-NetFirewallRule -DisplayName "Mobile Money Replication" -Direction Inbound -Protocol UDP -LocalPort 6101-6110 -Action Allow
```

```bash
# Linux:
# Allow replication ports:
sudo ufw allow 6101:6110/udp
```

### Network Connectivity

**Test connectivity between machines:**

```bash
# From Machine 1, ping Machine 2:
ping 10.29.42.56

# If ping works, network sync will work!
```

---

## 🐛 Troubleshooting

### "No servers responded"

**Cause:** Servers not running or network not accessible

**Solution:**
```bash
# 1. Check servers are running:
# Look for "Ready!" message on each server

# 2. Check network connectivity:
ping 10.29.42.224  # Server 1
ping 10.29.42.56   # Server 10

# 3. Check firewall:
# Make sure UDP ports 6101-6110 are open

# 4. Check servers.json:
# Make sure IPs are correct
```

### "Timeout waiting for server"

**Cause:** Server not responding or network slow

**Solution:**
```bash
# 1. Increase timeout in network_sync.py:
# Change: self.timeout = 10.0
# To:     self.timeout = 30.0

# 2. Check server logs:
# Look for errors on server

# 3. Check network latency:
ping -n 10 10.29.42.56
# Should be < 100ms
```

### "Some servers did not respond"

**Cause:** Some servers offline or unreachable

**Solution:**
```bash
# Sync will still work for responding servers!
# 
# Start missing servers and run sync again:
python server.py <missing_id>
python network_sync.py
```

### "Failed to add/update account"

**Cause:** Server rejected the update

**Solution:**
```bash
# Check server logs for errors
# Server might be overloaded or database locked
# 
# Try again:
python network_sync.py
```

---

## 📊 Comparison: network_sync.py vs peer_sync.py

| Feature | network_sync.py | peer_sync.py |
|---------|----------------|--------------|
| **Works across machines** | ✅ Yes | ❌ No (local only) |
| **Servers must be running** | ✅ Yes | ❌ No (stopped) |
| **Requires network access** | ✅ Yes | ❌ No |
| **Direct database access** | ❌ No | ✅ Yes |
| **Speed** | Slower (network) | Faster (local) |
| **Use case** | Different machines | Same machine |

---

## 🎯 Best Practices

### 1. Run After Adding New Server

```bash
# Add Server 10 on new machine:
# 1. Update servers.json and config.py
# 2. Start Server 10:
python server.py 10

# 3. Run network sync:
python network_sync.py

# 4. Done! Server 10 has all data
```

### 2. Run Periodically to Ensure Consistency

```bash
# Run once per day to ensure all servers in sync:
python network_sync.py

# Or create a cron job (Linux):
0 2 * * * cd /path/to/mobile-money && python network_sync.py
```

### 3. Run After Network Issues

```bash
# If network was down and servers got out of sync:
python network_sync.py

# This will re-sync all servers
```

### 4. Check Before and After

```bash
# Before sync:
python compare_databases.py

# Run sync:
python network_sync.py

# After sync:
python compare_databases.py
# Should show no differences!
```

---

## 🔍 Verification

### Verify Sync Worked

```bash
# Method 1: Check with client
python client.py

# 1. Connect to Server 1
# 2. Login with account
# 3. Check balance

# 4. Switch to Server 10
# 5. Login with same account
# 6. Check balance

# If balances match, sync worked! ✅

# Method 2: Compare databases
python compare_databases.py

# Should show:
# ✓ All servers have same data
```

---

## 💡 Advanced Usage

### Sync Specific Servers Only

Edit `network_sync.py` to filter servers:

```python
# Only sync servers 1 and 10:
servers = [s for s in config.get_active_servers() if s['id'] in [1, 10]]
```

### Sync from Command Line

```bash
# Sync all servers:
python network_sync.py

# No interaction needed (for automation):
echo "" | python network_sync.py
```

### Monitor Sync Progress

```bash
# Redirect output to log file:
python network_sync.py > sync.log 2>&1

# Check log:
cat sync.log
```

---

## 📚 Summary

**`network_sync.py` is the solution for syncing servers across different machines!**

### Key Points:
- ✅ Works across different machines
- ✅ Servers must be running
- ✅ Uses network communication (UDP)
- ✅ No server restart needed
- ✅ Handles chunked data transfer
- ✅ Last-Writer-Wins conflict resolution

### Typical Workflow:
```bash
# 1. Start all servers (on different machines)
python server.py 1   # Machine 1
python server.py 10  # Machine 2

# 2. Run network sync (from any machine)
python network_sync.py

# 3. Done! All servers synced
```

---

## 🎉 Answer to Your Question

**Q: If I add Server 10 on a different machine and run network sync, will it get the data?**

**A: YES! ✅**

Here's exactly what happens:

```bash
# Machine 1: Server 1 running with 14 accounts
# Machine 2: Server 10 just started (empty)

# Run network sync:
python network_sync.py

# Result:
# - network_sync.py connects to Server 1 via network
# - Gets all 14 accounts from Server 1
# - Connects to Server 10 via network
# - Sends all 14 accounts to Server 10
# - Server 10 now has all 14 accounts! ✅

# No restart needed!
# Works across different machines!
```

**This is exactly what you need!** 🚀

---

**Sync servers across different machines with ease!** 🌐✨
