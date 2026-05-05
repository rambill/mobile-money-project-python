# How to Sync Your Databases

## Problem Summary

You have **different balances** on your two servers:
- **Server 1 (10.29.42.224):** Account 0759016809 has balance **54,000**
- **Server 2 (10.29.42.65):** Account 0759016809 has balance **2,000**

This happened because the servers were running **without proper replication** due to a config error.

## What Was Fixed

✅ **Fixed `config.py`** - Removed invalid triple-quoted string syntax that was breaking the config
✅ **`servers.json` is already correct** - Has valid JSON with your 2 server IPs

## Now You Need to Sync the Databases

You have **3 options**. Choose the one that makes sense for your situation:

---

## Option A: Keep Server 1 Data (Balance: 54,000) ⭐ RECOMMENDED

Use this if Server 1 has the **correct** balance.

### Steps:

1. **Stop both servers** (press `Ctrl+C` in each terminal)

2. **On Server 2 machine (10.29.42.65):**
   ```bash
   del data\server_2.db
   ```

3. **Restart Server 1 first (on 10.29.42.224):**
   ```bash
   python server.py 1
   ```

4. **Restart Server 2 (on 10.29.42.65):**
   ```bash
   python server.py 2
   ```

5. **Test replication:**
   - Login on Server 1: Account 0759016809, PIN 1111
   - Check balance: Should show **54,000**
   - Login on Server 2: Same account
   - Check balance: Should show **54,000** (replicated!)

---

## Option B: Keep Server 2 Data (Balance: 2,000)

Use this if Server 2 has the **correct** balance.

### Steps:

1. **Stop both servers** (press `Ctrl+C` in each terminal)

2. **On Server 1 machine (10.29.42.224):**
   ```bash
   del data\server_1.db
   ```

3. **Restart Server 2 first (on 10.29.42.65):**
   ```bash
   python server.py 2
   ```

4. **Restart Server 1 (on 10.29.42.224):**
   ```bash
   python server.py 1
   ```

5. **Test replication:**
   - Login on Server 2: Account 0759016809, PIN 1111
   - Check balance: Should show **2,000**
   - Login on Server 1: Same account
   - Check balance: Should show **2,000** (replicated!)

---

## Option C: Start Fresh (Clean Slate)

Use this if you want to **start over** with a clean database.

### Steps:

1. **Stop both servers** (press `Ctrl+C` in each terminal)

2. **On Server 1 machine (10.29.42.224):**
   ```bash
   del data\server_1.db
   ```

3. **On Server 2 machine (10.29.42.65):**
   ```bash
   del data\server_2.db
   ```

4. **Restart both servers:**
   ```bash
   # On Server 1 machine:
   python server.py 1
   
   # On Server 2 machine:
   python server.py 2
   ```

5. **Register account again:**
   ```bash
   python client.py
   # Choose option 1: Register
   # Phone: 0759016809
   # PIN: 1111
   ```

6. **Test replication:**
   - Deposit 10,000 on Server 1
   - Check balance on Server 2: Should show **10,000** (replicated!)

---

## How to Verify Replication is Working

After following one of the options above:

### Test 1: Deposit on Server 1, Check on Server 2

```bash
# On Server 1 machine:
python client.py
# Login: 0759016809, PIN: 1111
# Deposit: 5,000
# Check balance: Note the amount

# On Server 2 machine:
python client.py
# Login: 0759016809, PIN: 1111
# Check balance: Should match Server 1!
```

### Test 2: Withdraw on Server 2, Check on Server 1

```bash
# On Server 2 machine:
python client.py
# Login: 0759016809, PIN: 1111
# Withdraw: 1,000
# Check balance: Note the amount

# On Server 1 machine:
python client.py
# Login: 0759016809, PIN: 1111
# Check balance: Should match Server 2!
```

### What You Should See in Server Logs

When replication is working, you'll see messages like:

```
[Server 1] Replicated DEPOSIT for 0759016809: 5000.0
[Server 2] Replicated WITHDRAW for 0759016809: 1000.0
```

---

## Troubleshooting

### Still seeing different balances?

1. **Check if servers loaded the correct config:**
   - Look at server startup logs
   - Should show: `[Server 1] Initializing Kampala...`
   - Should show: `[Server 2] Initializing Mbarara...`

2. **Check network connectivity:**
   ```bash
   # From Server 1, ping Server 2:
   ping 10.29.42.65
   
   # From Server 2, ping Server 1:
   ping 10.29.42.224
   ```

3. **Check firewall:**
   - Make sure ports **6101** and **6102** are open for UDP traffic
   - These are the replication ports

4. **Check server logs for errors:**
   - Look for messages like "Failed to replicate to server X"
   - If you see timeout errors, check network/firewall

### Replication is slow?

- This is normal! Replication happens in the background
- Wait 1-2 seconds after an operation before checking the other server
- The system uses UDP which is fast but fire-and-forget

---

## Summary

1. ✅ **Config is now fixed** - `config.py` has valid Python syntax
2. ✅ **servers.json is correct** - Has your 2 server IPs
3. ⚠️ **Databases are out of sync** - Choose Option A, B, or C above
4. 🎯 **After syncing** - Test replication to verify it works

**Recommended:** Use **Option A** (keep Server 1 data with 54,000 balance)

---

## Quick Commands Reference

### Windows Commands:
```bash
# Delete a file:
del data\server_1.db

# Delete multiple files:
del data\server_1.db data\server_2.db

# Start server:
python server.py 1

# Start client:
python client.py
```

### Check if config loads correctly:
```bash
python -c "import config; print(config.SERVERS)"
```

Should show your 2 servers with the correct IPs!

---

**After following these steps, your replication should work perfectly!** 🚀
