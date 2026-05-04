# Fix Replication Issue

## Problem

You have different balances on different servers:
- **Server 1:** Account 0759016809 has balance 54000
- **Server 2:** Account 0759016809 has balance 2000

This means **replication was not working**.

## Root Cause

There were **TWO issues**:

1. **`servers.json`** had JSON comments (`/* */`), which are **not valid in JSON**
2. **`config.py`** had invalid Python syntax (triple-quoted string `"""` to comment out server 3)

Both issues caused the config to fail loading, so servers used the default config with `127.0.0.1` (localhost) instead of your actual IP addresses (`10.29.42.224` and `10.29.42.65`).

## Solution

### Step 1: Fix Configuration Files (Already Done ✅)

Both files have been fixed:

1. **`servers.json`** - Removed invalid JSON comments
2. **`config.py`** - Fixed Python syntax (removed triple-quoted string)

You can verify the fix by running:
```bash
python verify_config.py
```

This will show you if the config loads correctly and displays your server IPs.

### Step 2: Check Current Data

```bash
python sync_servers.py
```

This will show you the differences between the two servers.

### Step 3: Choose Your Fix

You have 3 options:

#### Option A: Use Server 1 as Source of Truth (Recommended if Server 1 has correct data)

```bash
# 1. Stop both servers (Ctrl+C in each terminal)

# 2. Delete Server 2's database
rm data/server_2.db
# Windows: del data\server_2.db

# 3. Restart Server 1 (on machine 10.29.42.224)
python server.py 1

# 4. Restart Server 2 (on machine 10.29.42.65)
python server.py 2

# Server 2 will start with empty database
# When you make operations, they will replicate correctly
```

#### Option B: Use Server 2 as Source of Truth (If Server 2 has correct data)

```bash
# 1. Stop both servers (Ctrl+C in each terminal)

# 2. Delete Server 1's database
rm data/server_1.db
# Windows: del data\server_1.db

# 3. Restart Server 2 (on machine 10.29.42.65)
python server.py 2

# 4. Restart Server 1 (on machine 10.29.42.224)
python server.py 1
```

#### Option C: Start Fresh (Recommended if both have incorrect data)

```bash
# 1. Stop both servers (Ctrl+C in each terminal)

# 2. Delete both databases
rm data/server_1.db data/server_2.db
# Windows: del data\server_1.db data\server_2.db

# 3. Restart Server 1 (on machine 10.29.42.224)
python server.py 1

# 4. Restart Server 2 (on machine 10.29.42.65)
python server.py 2

# 5. Register account again and start fresh
```

### Step 4: Verify Replication Works

After restarting servers:

```bash
# On Server 1 machine (10.29.42.224)
python client.py

# Register or login
Option 2: Login (0759016809, PIN: 1111)

# Deposit money
Option 4: Deposit 1000

# Note the balance
Option 3: Check balance
# Should show: 55000 (or 3000 if you started fresh)
```

Then on Server 2:

```bash
# On Server 2 machine (10.29.42.65)
python client.py

# Login with same account
Option 2: Login (0759016809, PIN: 1111)

# Check balance
Option 3: Check balance
# Should show: SAME balance as Server 1!
```

## How to Prevent This

### 1. Don't Use Comments in JSON

**Wrong:**
```json
{
  "servers": [
    {"id": 1, ...},
    /* This is a comment - DON'T DO THIS! */
    {"id": 2, ...}
  ]
}
```

**Right:**
```json
{
  "servers": [
    {"id": 1, ...},
    {"id": 2, ...}
  ]
}
```

### 2. To Disable a Server, Use "active": false

**Instead of commenting out:**
```json
{
  "servers": [
    {"id": 1, "active": true},
    {"id": 2, "active": true},
    {"id": 3, "active": false}  ← Disabled, but valid JSON
  ]
}
```

### 3. Check Config Loads Correctly

After editing `servers.json`, verify it loads:

```bash
python -c "import json; print(json.load(open('servers.json')))"
```

If you see an error, fix the JSON syntax.

## Troubleshooting

### Replication Still Not Working?

1. **Check firewall:**
   ```bash
   # On Server 2 machine, test if you can reach Server 1
   nc -u 10.29.42.224 6101
   ```

2. **Check server logs:**
   Look for messages like:
   ```
   [Server 1] Replicated DEPOSIT for 0759016809: 1000.0
   ```

3. **Check network connectivity:**
   ```bash
   ping 10.29.42.224
   ping 10.29.42.65
   ```

### Different Balances After Fix?

If you still see different balances:

1. **Stop both servers**
2. **Run sync script:**
   ```bash
   python sync_servers.py
   ```
3. **Follow the recommendations**

## Summary

✅ **Fixed:** servers.json (removed invalid comments)  
✅ **Next:** Choose Option A, B, or C to sync data  
✅ **Verify:** Test replication works  
✅ **Prevent:** Don't use comments in JSON  

## Quick Fix Commands

### If Server 1 has correct data (54000):
```bash
# Stop both servers
# On Server 2 machine:
rm data/server_2.db
python server.py 2

# On Server 1 machine:
python server.py 1
```

### If Server 2 has correct data (2000):
```bash
# Stop both servers
# On Server 1 machine:
rm data/server_1.db
python server.py 1

# On Server 2 machine:
python server.py 2
```

### If starting fresh:
```bash
# Stop both servers
# On both machines:
rm data/server_*.db

# Restart both servers
python server.py 1  # On Server 1 machine
python server.py 2  # On Server 2 machine
```

---

**After following these steps, replication should work correctly!** 🎉
