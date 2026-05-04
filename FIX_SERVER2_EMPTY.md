# Fix: Server 2 Database is Empty

## Problem

After deleting Server 2's database and restarting:
- ✓ Server 1 works fine (has account 0759016809 with balance 54,000)
- ✗ Server 2 shows "Account not found" or "Invalid PIN"

**Why?** Replication only works for **NEW operations**. Existing accounts on Server 1 were never replicated to the new empty Server 2 database.

---

## Solution: Copy Database File

The **easiest solution** is to copy Server 1's database to Server 2.

### Option 1: Copy on Same Machine (If both servers on same PC)

```bash
# 1. Stop Server 2 (Ctrl+C)

# 2. Copy database file:
copy data\server_1.db data\server_2.db

# 3. Restart Server 2:
python server.py 2

# 4. Test on Server 2:
python client.py
# Login: 0759016809, PIN: 1111
# Should work now!
```

### Option 2: Copy Between Machines (Your Setup)

Since your servers are on **different machines**, you need to transfer the file:

#### On Server 1 Machine (10.29.42.224):

```bash
# 1. Stop Server 1 (Ctrl+C)

# 2. Copy database to a USB drive or shared folder
# Or use network share
```

#### On Server 2 Machine (10.29.42.65):

```bash
# 1. Stop Server 2 (Ctrl+C)

# 2. Delete the empty database:
del data\server_2.db

# 3. Copy server_1.db from USB/network to data folder

# 4. Rename it to server_2.db:
ren data\server_1.db server_2.db

# 5. Restart Server 2:
python server.py 2

# 6. Restart Server 1 (on Server 1 machine):
python server.py 1
```

---

## Alternative: Use Python Script

If you can't easily transfer files, use the script:

```bash
# On Server 2 machine:
python sync_from_server1.py

# Follow the prompts:
# - Enter phone: 0759016809
# - Enter PIN: 1111
```

This will:
1. Connect to Server 1
2. Fetch account data
3. Insert it into Server 2 database

---

## After Copying Database

### Test Replication:

```bash
# On Server 1:
python client.py
# Login: 0759016809, PIN: 1111
# Deposit: 5000
# Check balance: Should show 59000

# On Server 2:
python client.py
# Login: 0759016809, PIN: 1111
# Check balance: Should show 59000 (replicated!)
```

### What You Should See:

**Server 1 logs:**
```
[Server 1] DEPOSIT request: phone=0759016809, pin=****, amount=5000.0
```

**Server 2 logs:**
```
[Server 2] Replicated DEPOSIT for 0759016809: 5000.0
```

---

## Why This Happened

The replication system works like this:

1. **New operations** (REGISTER, DEPOSIT, WITHDRAW, TRANSFER) are replicated in real-time
2. **Existing data** is NOT automatically synced when a server starts with empty database

So when you:
1. Deleted Server 2's database → Server 2 became empty
2. Restarted Server 2 → It started with empty database
3. Tried to login → Account doesn't exist on Server 2!

**Solution:** Copy the database OR register the account again.

---

## Quick Fix Summary

**Easiest method:**

1. Stop both servers
2. Copy `data\server_1.db` to Server 2 machine
3. Rename to `data\server_2.db` on Server 2 machine
4. Restart both servers
5. Test - should work!

**Alternative method:**

1. Keep both servers running
2. On Server 2 machine: `python sync_from_server1.py`
3. Enter account details
4. Test - should work!

---

## Future: Avoid This Issue

To avoid this in the future:

### Option A: Don't Delete Databases

Instead of deleting databases, let the anti-entropy/gossip system sync them automatically (runs every 60 seconds).

### Option B: Register Account Again

If you delete a database, just register the account again:

```bash
# On Server 2:
python client.py
# Option 1: Register
# Phone: 0759016809
# PIN: 1111
# Deposit: 54000
```

This will replicate to Server 1, and the system will handle conflicts.

---

## Need Help?

If copying the database doesn't work:

1. **Check file exists:**
   ```bash
   dir data\server_1.db  # Should show file size
   dir data\server_2.db  # Should show same size
   ```

2. **Check database contents:**
   ```bash
   python -c "import sqlite3; conn = sqlite3.connect('data/server_2.db'); print(conn.execute('SELECT COUNT(*) FROM accounts').fetchone()[0])"
   ```
   Should show: `1` (one account)

3. **Check server logs:**
   - Server 2 should show: `[Server 2] Using existing database`

---

**After copying the database, both servers will have the same data and replication will work for new operations!** 🚀
