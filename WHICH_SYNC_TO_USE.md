# 🤔 Which Sync Script to Use?

## Quick Decision Guide

```
Do you have one "main" server with correct data?
    ├─ YES → Use force_sync.py (Master-Slave)
    └─ NO → Use peer_sync.py (Peer-to-Peer)

Do all servers have unique/different data to share?
    ├─ YES → Use peer_sync.py (Peer-to-Peer)
    └─ NO → Use force_sync.py (Master-Slave)

Do you want true distributed peer-to-peer?
    ├─ YES → Use peer_sync.py (Peer-to-Peer)
    └─ NO → Use force_sync.py (Master-Slave)
```

---

## Comparison

| Feature | force_sync.py | peer_sync.py |
|---------|---------------|--------------|
| **Architecture** | Master-Slave | Peer-to-Peer |
| **Server 1 Role** | Master (source of truth) | Equal peer |
| **Data Flow** | One-way (Server 1 → Others) | Multi-way (All ←→ All) |
| **Conflict Resolution** | Server 1 always wins | Last-Writer-Wins (newest) |
| **Use Case** | One server has correct data | All servers contribute data |
| **Philosophy** | Centralized | Distributed |

---

## force_sync.py (Master-Slave)

### Architecture

```
Server 1 (Master)
    ↓
    ├─→ Server 2
    ├─→ Server 3
    ├─→ Server 4
    └─→ Server 5

One-way sync: Server 1 → All others
```

### When to Use

✅ **Use when:**
- Server 1 has the correct/complete data
- Other servers are out of sync
- You want one source of truth
- Simple master-slave architecture

❌ **Don't use when:**
- Multiple servers have unique data
- You want true peer-to-peer
- No single master server

### Example

```bash
# Scenario: Server 1 has 14 accounts (correct)
#           Server 2 has 13 accounts (missing 1)
#           Server 3 is empty

python force_sync.py

# Result: All servers have 14 accounts from Server 1
```

---

## peer_sync.py (Peer-to-Peer)

### Architecture

```
Server 1 ←→ Server 2
    ↕         ↕
Server 3 ←→ Server 4
    ↕         ↕
Server 5 ←→ ...

Multi-way sync: All ←→ All
```

### When to Use

✅ **Use when:**
- All servers have unique data to contribute
- No single master server
- Want true distributed system
- Servers have different/conflicting data

❌ **Don't use when:**
- One server has all correct data
- Want simple master-slave
- Don't need peer-to-peer

### Example

```bash
# Scenario: Server 1 has accounts A, B, C
#           Server 2 has accounts D, E, F
#           Server 3 has accounts G, H, I

python peer_sync.py

# Result: All servers have accounts A-I
#         Each server contributed its unique data
```

---

## Real-World Scenarios

### Scenario 1: Initial Setup

**Situation:** Setting up new cluster, Server 1 has all data

**Solution:** `force_sync.py`

```bash
# Server 1 has 100 accounts
# Servers 2, 3, 4, 5 are empty

python force_sync.py

# All servers get 100 accounts from Server 1
```

---

### Scenario 2: Regional Servers

**Situation:** Each server has accounts from its region

**Solution:** `peer_sync.py`

```bash
# Server 1 (Kampala): 50 accounts from Central
# Server 2 (Mbarara): 30 accounts from Western
# Server 3 (Gulu): 20 accounts from Northern

python peer_sync.py

# All servers get all 100 accounts
# Each region's data is shared with all servers
```

---

### Scenario 3: Out of Sync

**Situation:** Servers have same accounts but different balances

**Solution:** `peer_sync.py` (uses newest data)

```bash
# Server 1: Account X = 1000 (modified today)
# Server 2: Account X = 500  (modified yesterday)
# Server 3: Account X = 2000 (modified last week)

python peer_sync.py

# All servers: Account X = 1000 (newest from Server 1)
```

---

### Scenario 4: Disaster Recovery

**Situation:** Server 1 has backup, others corrupted

**Solution:** `force_sync.py`

```bash
# Server 1 has correct backup data
# Servers 2, 3, 4 have corrupted data

python force_sync.py

# All servers restored from Server 1 backup
```

---

## Conflict Resolution

### force_sync.py

```
Conflict: Server 1 vs Server 2 have different data
Resolution: Server 1 always wins (it's the master)

Example:
Server 1: Account X = 1000
Server 2: Account X = 500

Result: Both servers have 1000 (from Server 1)
```

### peer_sync.py

```
Conflict: Multiple servers have different data
Resolution: Last-Writer-Wins (newest timestamp)

Example:
Server 1: Account X = 1000 (timestamp: 10:00 AM)
Server 2: Account X = 500  (timestamp: 9:00 AM)

Result: Both servers have 1000 (newest from Server 1)
```

---

## Performance

### force_sync.py

```
Speed: Fast (one-way copy)
Complexity: Low
Network: Not needed (direct database access)
```

### peer_sync.py

```
Speed: Slightly slower (merge + distribute)
Complexity: Medium (conflict resolution)
Network: Not needed (direct database access)
```

---

## Recommendations

### For Your Current Situation

**You have:**
- Server 1: 14 accounts
- Server 2: 13 accounts (missing 1, different balances)

**Recommendation:** Use `force_sync.py`

**Why:**
- Server 1 has the correct data
- Server 2 is just out of sync
- Simple master-slave is sufficient

**Command:**
```bash
python force_sync.py
```

---

### For Future (Adding Servers 3, 4, 5)

**If:** New servers are empty

**Recommendation:** Use `force_sync.py`

**Why:**
- Server 1 has all the data
- New servers just need to receive it

**Command:**
```bash
python force_sync.py
```

---

**If:** Each server will have unique regional data

**Recommendation:** Use `peer_sync.py`

**Why:**
- Each server contributes unique data
- True peer-to-peer needed

**Command:**
```bash
python peer_sync.py
```

---

## Summary

### force_sync.py
- **Architecture:** Master-Slave
- **Use when:** One server has correct data
- **Result:** All servers match Server 1

### peer_sync.py
- **Architecture:** Peer-to-Peer
- **Use when:** All servers contribute data
- **Result:** All servers have union of all data

### Your Situation
**Current:** Use `force_sync.py` (Server 1 has correct data)  
**Future:** Use `peer_sync.py` if servers have unique regional data

---

**Both scripts work! Choose based on your architecture!** 🚀

**Master-Slave or Peer-to-Peer - you decide!** ✨
