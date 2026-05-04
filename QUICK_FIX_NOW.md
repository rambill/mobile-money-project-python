# 🚨 QUICK FIX - Server 2 Empty Database

## Your Problem

✓ Server 1 works (account exists)  
✗ Server 2 shows "Account not found" or "Invalid PIN"

**Reason:** Server 2's database is empty after you deleted it.

---

## Quick Fix (Choose One)

### Method 1: Copy Database File ⭐ EASIEST

Since your servers are on **different machines**, you need to transfer the database file:

#### Step 1: On Server 1 Machine (10.29.42.224)

```bash
# Stop Server 1 (Ctrl+C)

# The database file is at: data\server_1.db
# Copy this file to a USB drive or network share
```

#### Step 2: On Server 2 Machine (10.29.42.65)

```bash
# Stop Server 2 (Ctrl+C)

# Delete empty database:
del data\server_2.db

# Copy server_1.db from USB/network to data folder
# Then rename it:
ren data\server_1.db server_2.db
```

#### Step 3: Restart Both Servers

```bash
# On Server 1 machine:
python server.py 1

# On Server 2 machine:
python server.py 2
```

#### Step 4: Test

```bash
# On Server 2 machine:
python client.py
# Login: 0759016809, PIN: 1111
# Check balance: Should show 54000!
```

---

### Method 2: Register Account Again ⭐ SIMPLEST

Just register the account again on Server 2:

```bash
# On Server 2 machine:
python client.py

# Option 1: Register new account
# Phone: 0759016809
# PIN: 1111

# Option 4: Deposit money
# Amount: 54000

# This will replicate to Server 1
```

**Note:** This creates a new account with balance 54000. The system will handle any conflicts.

---

### Method 3: Use Sync Script

```bash
# On Server 2 machine (with both servers running):
python sync_from_server1.py

# Enter phone: 0759016809
# Enter PIN: 1111

# Script will fetch data from Server 1 and insert into Server 2
```

---

## Which Method to Use?

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **Copy Database** | Exact copy, preserves all data | Need to transfer file between machines | Production, multiple accounts |
| **Register Again** | Super simple, no file transfer | Creates new account, might have conflicts | Testing, single account |
| **Sync Script** | Automated, no file transfer | Requires both servers running | Quick fix, single account |

---

## Recommended: Method 2 (Register Again)

Since you only have **one account** (0759016809), the simplest solution is:

```bash
# On Server 2 machine:
python client.py

# 1. Register
Phone: 0759016809
PIN: 1111

# 2. Deposit
Amount: 54000

# 3. Check balance
Should show: 54000

# 4. Test replication - deposit 1000 on Server 2
# 5. Check balance on Server 1 - should show 55000!
```

---

## After Fix - Test Replication

```bash
# On Server 2:
python client.py
# Login: 0759016809, PIN: 1111
# Deposit: 1000
# Balance: 55000

# On Server 1:
python client.py
# Login: 0759016809, PIN: 1111
# Balance: 55000 ← Should match!
```

If balances match → **Replication is working!** ✅

---

## Summary

**Problem:** Server 2 database is empty  
**Solution:** Copy database OR register account again  
**Recommended:** Register account again (simplest for single account)

**Next:** Test replication by making transactions on both servers

---

**Choose Method 2 (Register Again) - it's the fastest!** 🚀
