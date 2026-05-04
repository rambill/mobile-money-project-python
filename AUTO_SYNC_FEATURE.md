# ✨ Automatic State Synchronization

## What's New?

Your distributed mobile money system now has **automatic state synchronization**! 

When a new server joins the cluster or starts with an empty database, it will **automatically sync all data** from existing servers.

---

## How It Works

### 1. **Startup Detection**

When a server starts, it checks if its database is empty:

```
[Server 2] Starting on 10.29.42.65:6002...
[Server 2] Database is empty, requesting state from peers...
```

### 2. **State Request**

The server automatically requests full state from a peer:

```
[Server 2] Requesting full state from Server 1...
[Server 1] Received state request from Server 2
[Server 1] Sending 5 account(s) to Server 2
```

### 3. **Automatic Sync**

All accounts are synced automatically:

```
[Server 2] Received 5 account(s) from Server 1
[Server 2] ✓ Initial state sync complete: 5 account(s) synced from Server 1
```

### 4. **Ready to Use**

Server 2 now has all the data and is ready for transactions!

---

## Benefits

✅ **No Manual Scripts** - No need to run `sync_from_server1.py` or copy database files  
✅ **Automatic** - Happens on startup without any user intervention  
✅ **Scalable** - Works when adding 3rd, 4th, 5th server...  
✅ **Reliable** - Tries multiple peers if one fails  
✅ **Fast** - Syncs in seconds on startup  

---

## Usage Examples

### Example 1: Adding Server 2 to Existing Server 1

```bash
# Server 1 is already running with data
# On Server 1 machine:
python server.py 1

# On Server 2 machine (new/empty):
python server.py 2

# Output on Server 2:
# [Server 2] Database is empty, requesting state from peers...
# [Server 2] Requesting full state from Server 1...
# [Server 2] Received 3 account(s) from Server 1
# [Server 2] ✓ Initial state sync complete: 3 account(s) synced from Server 1

# Now test on Server 2:
python client.py
# Login: 0759016809, PIN: 1111
# Check balance: Shows correct balance from Server 1!
```

### Example 2: Adding Server 3 to Existing Cluster

```bash
# Servers 1 and 2 are already running
# On Server 3 machine:
python server.py 3

# Output:
# [Server 3] Database is empty, requesting state from peers...
# [Server 3] Requesting full state from Server 1...
# [Server 3] ✓ Initial state sync complete: 10 account(s) synced from Server 1

# Server 3 now has all data from the cluster!
```

### Example 3: Recovering from Database Deletion

```bash
# Accidentally deleted Server 2's database
del data\server_2.db

# Just restart Server 2:
python server.py 2

# It will automatically sync from Server 1!
# No manual intervention needed!
```

---

## Configuration

The feature is controlled by `config.py`:

```python
STATE_SYNC_ON_STARTUP = True  # Enable automatic state sync
```

To disable (not recommended):

```python
STATE_SYNC_ON_STARTUP = False
```

---

## How It's Different from Replication

| Feature | Replication | Auto State Sync |
|---------|-------------|-----------------|
| **When** | Ongoing, for new operations | Once, on startup |
| **What** | Individual transactions | Full database state |
| **Trigger** | Client operations | Empty database detected |
| **Purpose** | Keep servers in sync | Bootstrap new servers |

**Both work together:**
1. **Auto State Sync** - Gets initial data when server starts empty
2. **Replication** - Keeps servers in sync for new operations

---

## Technical Details

### State Request Protocol

1. **New server** sends `STATE_REQUEST` message to peer
2. **Peer server** responds with all accounts (phone, PIN, balance, vector clock)
3. **New server** inserts accounts into local database
4. **New server** is now ready for normal operations

### Peer Selection

- Tries peers in order from `servers.json`
- If first peer fails, tries next peer
- Continues until successful or all peers exhausted

### Conflict Handling

- Only syncs if database is **completely empty** (0 accounts)
- If database has data, skips sync (assumes it's valid)
- Duplicate accounts are skipped (won't overwrite existing data)

---

## Troubleshooting

### Server doesn't sync automatically

**Check 1: Is database really empty?**

```bash
python -c "import sqlite3; conn = sqlite3.connect('data/server_2.db'); print(conn.execute('SELECT COUNT(*) FROM accounts').fetchone()[0])"
```

If it shows `> 0`, the database is not empty, so sync is skipped.

**Check 2: Are peers reachable?**

```bash
ping 10.29.42.224  # Ping Server 1
```

**Check 3: Are peers running?**

Make sure at least one other server is running before starting the new server.

**Check 4: Check server logs**

Look for messages like:
```
[Server 2] Requesting full state from Server 1...
[Server 2] Failed to get state from Server 1: No response
```

This indicates network or firewall issues.

### Sync is slow

- Normal sync time: 1-5 seconds for 100 accounts
- If slower, check network latency between servers
- Large databases (1000+ accounts) may take longer

### Sync fails with "No response"

**Possible causes:**
1. Peer server is not running
2. Firewall blocking replication port (6101, 6102)
3. Network connectivity issue
4. Peer server is overloaded

**Solution:**
- Verify peer is running: Check if you see `[Server 1] Ready!`
- Check firewall: Allow UDP ports 6101, 6102
- Check network: `ping <peer_ip>`

---

## Testing the Feature

### Test 1: Fresh Server Sync

```bash
# 1. Start Server 1 with data
python server.py 1

# 2. Create an account
python client.py
# Register: 0759016809, PIN: 1111
# Deposit: 10000

# 3. Start Server 2 (empty database)
python server.py 2

# 4. Check Server 2 logs - should see:
# [Server 2] ✓ Initial state sync complete: 1 account(s) synced

# 5. Test on Server 2
python client.py
# Login: 0759016809, PIN: 1111
# Balance: 10000 ← Synced from Server 1!
```

### Test 2: Multiple Accounts

```bash
# 1. Create multiple accounts on Server 1
python client.py
# Register: 0759111111, PIN: 1111
# Register: 0759222222, PIN: 2222
# Register: 0759333333, PIN: 3333

# 2. Start Server 2
python server.py 2

# 3. Should sync all 3 accounts automatically

# 4. Verify on Server 2
python client.py
# Login with each account - all should work!
```

### Test 3: Adding Third Server

```bash
# 1. Servers 1 and 2 are running with data

# 2. Add servers.json entry for Server 3:
{
  "id": 3,
  "host": "10.29.42.146",
  "port": 6003,
  "rep_port": 6103,
  "active": true
}

# 3. Start Server 3
python server.py 3

# 4. Should sync from Server 1 or 2 automatically

# 5. Test on Server 3 - all accounts should work!
```

---

## What You Don't Need Anymore

❌ **Manual database copying** - No need to copy `server_1.db` to `server_2.db`  
❌ **Sync scripts** - No need to run `sync_from_server1.py`  
❌ **Re-registering accounts** - No need to register accounts again on new servers  
❌ **Manual state transfer** - Everything happens automatically  

---

## Summary

🎉 **Your system now has automatic state synchronization!**

**What this means:**
- Add new servers anytime - they sync automatically
- Delete a database - just restart, it syncs automatically
- Scale to 3, 4, 5+ servers - all sync automatically
- No manual intervention needed

**How to use:**
1. Start existing servers with data
2. Start new server with empty database
3. Wait 3-5 seconds
4. New server is ready with all data!

**Next steps:**
- Test by deleting Server 2's database and restarting
- Add a third server and watch it sync automatically
- Enjoy hassle-free distributed system management!

---

**The feature is already enabled and ready to use!** 🚀
