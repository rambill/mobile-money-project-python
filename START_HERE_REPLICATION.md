# 🎯 START HERE - Fix Your Replication Issue

## Current Situation

✅ **Configuration is FIXED** - Both `config.py` and `servers.json` are now correct  
⚠️ **Databases are OUT OF SYNC** - You need to choose which data to keep

---

## Quick Fix (3 Steps)

### Step 1: Verify Config ✅

```bash
python verify_config.py
```

**Expected output:**
```
✓ config.py loads successfully
✓ Server 1 IP is correct: 10.29.42.224
✓ Server 2 IP is correct: 10.29.42.65
```

If you see this, **config is fixed!** ✅

---

### Step 2: Sync Databases ⚠️

You have different balances:
- **Server 1:** 54,000
- **Server 2:** 2,000

**Choose ONE option:**

#### Option A: Keep Server 1 Data (54,000) ⭐ RECOMMENDED

```bash
# 1. Stop both servers (Ctrl+C in each terminal)

# 2. On Server 2 machine (10.29.42.65):
del data\server_2.db

# 3. Restart Server 1 (on 10.29.42.224):
python server.py 1

# 4. Restart Server 2 (on 10.29.42.65):
python server.py 2
```

#### Option B: Keep Server 2 Data (2,000)

```bash
# 1. Stop both servers (Ctrl+C in each terminal)

# 2. On Server 1 machine (10.29.42.224):
del data\server_1.db

# 3. Restart Server 2 (on 10.29.42.65):
python server.py 2

# 4. Restart Server 1 (on 10.29.42.224):
python server.py 1
```

#### Option C: Start Fresh (Clean Slate)

```bash
# 1. Stop both servers (Ctrl+C in each terminal)

# 2. On BOTH machines:
del data\server_1.db  # On Server 1 machine
del data\server_2.db  # On Server 2 machine

# 3. Restart both servers:
python server.py 1  # On Server 1 machine
python server.py 2  # On Server 2 machine

# 4. Register account again:
python client.py
# Option 1: Register
# Phone: 0759016809, PIN: 1111
```

---

### Step 3: Test Replication 🧪

After syncing databases:

```bash
# On Server 1 machine:
python client.py
# Login: 0759016809, PIN: 1111
# Deposit: 5000
# Check balance: Note the amount (e.g., 59000)

# On Server 2 machine:
python client.py
# Login: 0759016809, PIN: 1111
# Check balance: Should show SAME amount (59000)!
```

**If balances match → Replication is working!** ✅

---

## What You Should See

### Server Logs (When Replication Works):

```
[Server 1] DEPOSIT request: phone=0759016809, pin=****, amount=5000.0
[Server 2] Replicated DEPOSIT for 0759016809: 5000.0
```

### Client Output (When Replication Works):

```
# On Server 1:
✓ Deposit successful
✓ Balance: UGX 59,000.00

# On Server 2 (same account):
✓ Balance: UGX 59,000.00  ← Same balance!
```

---

## Troubleshooting

### Still seeing different balances?

1. **Check server startup logs:**
   - Should show: `[Server 1] Initializing Kampala...`
   - Should show: `[Server 2] Initializing Mbarara...`

2. **Check network:**
   ```bash
   ping 10.29.42.224  # From Server 2
   ping 10.29.42.65   # From Server 1
   ```

3. **Check firewall:**
   - Ports 6101 and 6102 must be open for UDP

4. **Wait a moment:**
   - Replication happens in background (1-2 seconds)

---

## Summary

| Step | Status | Action |
|------|--------|--------|
| 1. Fix config | ✅ DONE | Run `python verify_config.py` to confirm |
| 2. Sync databases | ⚠️ TODO | Choose Option A, B, or C above |
| 3. Test replication | ⏳ PENDING | Deposit on one server, check on other |

---

## More Information

- **`SYNC_DATABASES.md`** - Detailed guide with all options
- **`verify_config.py`** - Script to verify configuration
- **`REPLICATION_FIXED.md`** - Summary of what was fixed
- **`FIX_REPLICATION.md`** - Technical details

---

## Quick Reference

```bash
# Verify config:
python verify_config.py

# Delete database:
del data\server_1.db  # Windows
del data\server_2.db  # Windows

# Start server:
python server.py 1  # Server 1
python server.py 2  # Server 2

# Start client:
python client.py
```

---

**Follow the 3 steps above and your replication will work!** 🚀

**Recommended:** Use **Option A** (keep Server 1 data with 54,000 balance)
