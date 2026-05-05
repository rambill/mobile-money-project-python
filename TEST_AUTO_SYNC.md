# 🧪 Test Automatic State Sync

## Quick Test (5 Minutes)

Follow these steps to test the new automatic state sync feature:

---

## Step 1: Prepare Server 1

```bash
# On Server 1 machine (10.29.42.224):

# Make sure Server 1 is running with your account
python server.py 1

# You should see:
# [Server 1] Starting on 10.29.42.224:6001...
# [Server 1] Using existing database
# [Server 1] Ready!
```

---

## Step 2: Delete Server 2 Database

```bash
# On Server 2 machine (10.29.42.65):

# Stop Server 2 if running (Ctrl+C)

# Delete the database:
del data\server_2.db

# Confirm it's deleted:
dir data\server_2.db
# Should show: File Not Found
```

---

## Step 3: Start Server 2 and Watch the Magic! ✨

```bash
# On Server 2 machine:
python server.py 2

# You should see:
# [Server 2] Starting on 10.29.42.65:6002...
# [Server 2] Creating new database at data\server_2.db
# [Server 2] Creating new database schema...
# [Server 2] Ready!
# [Server 2] Database is empty, requesting state from peers...
# [Server 2] Requesting full state from Server 1...
# [Server 2] Received X account(s) from Server 1
# [Server 2] ✓ Initial state sync complete: X account(s) synced from Server 1
```

**This is the automatic sync happening!** 🎉

---

## Step 4: Verify on Server 2

```bash
# On Server 2 machine:
python client.py

# Try to login with your account:
# Option 2: Login
# Phone: 0759016809
# PIN: 1111

# Check balance:
# Option 3: Check balance

# You should see the SAME balance as Server 1!
# This proves the account was synced automatically!
```

---

## Step 5: Test Replication (Both Directions)

### Test A: Deposit on Server 2, Check on Server 1

```bash
# On Server 2:
python client.py
# Login: 0759016809, PIN: 1111
# Deposit: 5000
# Note the new balance (e.g., 59000)

# On Server 1:
python client.py
# Login: 0759016809, PIN: 1111
# Check balance: Should show 59000 (replicated!)
```

### Test B: Withdraw on Server 1, Check on Server 2

```bash
# On Server 1:
python client.py
# Login: 0759016809, PIN: 1111
# Withdraw: 2000
# Note the new balance (e.g., 57000)

# On Server 2:
python client.py
# Login: 0759016809, PIN: 1111
# Check balance: Should show 57000 (replicated!)
```

---

## Expected Results

✅ **Server 2 syncs automatically** - No manual scripts needed  
✅ **Account exists on Server 2** - Can login immediately  
✅ **Balance matches Server 1** - Data is identical  
✅ **Replication works both ways** - Changes sync in real-time  

---

## What You Should See in Logs

### Server 1 Logs:
```
[Server 1] Starting on 10.29.42.224:6001...
[Server 1] Using existing database
[Server 1] Ready!
[Server 1] Received state request from Server 2
[Server 1] Sending 1 account(s) to Server 2
```

### Server 2 Logs:
```
[Server 2] Starting on 10.29.42.65:6002...
[Server 2] Creating new database schema...
[Server 2] Ready!
[Server 2] Database is empty, requesting state from peers...
[Server 2] Requesting full state from Server 1...
[Server 2] Received 1 account(s) from Server 1
[Server 2] ✓ Initial state sync complete: 1 account(s) synced from Server 1
```

---

## Troubleshooting

### "Could not sync state from any peer"

**Cause:** Server 1 is not running or not reachable

**Solution:**
1. Check Server 1 is running: `python server.py 1`
2. Check network: `ping 10.29.42.224`
3. Check firewall: Allow UDP port 6101

### "Database has X account(s), skipping initial sync"

**Cause:** Database is not empty

**Solution:**
1. Stop Server 2
2. Delete database: `del data\server_2.db`
3. Restart Server 2

### Account still not found on Server 2

**Cause:** Sync failed or didn't happen

**Solution:**
1. Check Server 2 logs for sync messages
2. Verify Server 1 is running
3. Try restarting Server 2

---

## Advanced Test: Add a Third Server

Want to test with 3 servers? Here's how:

### Step 1: Update servers.json

Add Server 3 to `servers.json`:

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
    }
  ]
}
```

### Step 2: Update config.py

Uncomment Server 3 in `config.py`:

```python
SERVERS = [
    # ... Server 1 and 2 ...
    {
        "id": 3,
        "name": "Gulu",
        "region": "Northern Uganda",
        "host": "10.29.42.146",
        "port": 6003,
        "rep_port": 6103,
        "active": True,
    },
]
```

### Step 3: Start Server 3

```bash
# On Server 3 machine (10.29.42.146):
python server.py 3

# Should see:
# [Server 3] Database is empty, requesting state from peers...
# [Server 3] ✓ Initial state sync complete: X account(s) synced
```

### Step 4: Test on Server 3

```bash
python client.py
# Login: 0759016809, PIN: 1111
# Should work immediately!
```

---

## Summary

**Before this feature:**
- ❌ Had to manually copy database files
- ❌ Had to run sync scripts
- ❌ Had to re-register accounts
- ❌ Complex setup for new servers

**After this feature:**
- ✅ Just start the server
- ✅ Automatic sync in 3-5 seconds
- ✅ Ready to use immediately
- ✅ Works for any number of servers

---

## Next Steps

1. **Test now:** Follow Steps 1-5 above
2. **Verify:** Check that balances match on both servers
3. **Enjoy:** Add more servers anytime, they sync automatically!

---

**The feature is ready to test! Just delete Server 2's database and restart it!** 🚀
