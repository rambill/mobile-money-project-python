# Quick Start Guide - Mobile Money System

Get up and running in 5 minutes!

## Prerequisites

- Python 3.8+ installed
- Terminal/Command Prompt access

## Step 1: Verify Python Installation

```bash
python --version
# Should show Python 3.8 or higher
```

## Step 2: Start Servers

### On Linux/macOS:

```bash
# Make scripts executable
chmod +x start_servers.sh stop_servers.sh

# Start all servers
./start_servers.sh
```

### On Windows:

```cmd
start_servers.bat
```

### Or Start Manually:

Open 3 separate terminals and run:

**Terminal 1:**
```bash
python server.py 1
```

**Terminal 2:**
```bash
python server.py 2
```

**Terminal 3:**
```bash
python server.py 3
```

You should see output like:
```
[Server 1] Initializing MoMo-Kampala...
[Server 1] Starting on 127.0.0.1:6001...
[Server 1] Starting election...
[Server 1] Ready!
```

## Step 3: Run Client

Open a new terminal:

```bash
python client.py
```

You'll see:
```
Discovering servers...
Found 3 server(s):
  1. MoMo-Kampala - 2.3ms
  2. MoMo-Mbarara - 3.1ms
  3. MoMo-Gulu - 2.8ms

Connected to: MoMo-Kampala
```

## Step 4: Try It Out!

### Register an Account

```
Select option: 1
Enter phone number: 256700123456
Enter 4-digit PIN: 1234

✓ Account created successfully
```

### Deposit Money

```
Select option: 4
Enter amount to deposit: 50000

✓ Success
  New balance: UGX 50,000.00
```

### Check Balance

```
Select option: 3

✓ Balance: UGX 50,000.00
```

### Withdraw Money

```
Select option: 5
Enter amount to withdraw: 10000

✓ Success
  New balance: UGX 40,000.00
```

## Step 5: Test Distributed Features

### Test Replication

1. Make a deposit on Server 1
2. Switch to Server 2 (option 6)
3. Check balance - should see the same amount!

### Test Failover

1. Stop one server (Ctrl+C in its terminal)
2. Client will automatically switch to another server
3. Continue using the system normally

## Admin Tools

### Check Server Status

```bash
python admin.py status
```

Output:
```
✓ Found 3 active server(s):

  Server 1: MoMo-Kampala
    Host: 127.0.0.1:6001
    Load: 15 requests
    Accounts: 5
    Transactions: 12
```

### Check Consistency

```bash
python admin.py sync
```

Output:
```
✓ All 5 accounts are consistent across servers!
```

### Run Tests

```bash
python admin.py test
```

Output:
```
Test 1: Account Registration
  ✓ Account 256700789012 registered successfully

Test 2: Deposit Money
  ✓ Deposited UGX 10,000

Test 3: Read-Your-Writes (Different Server)
  ✓ Balance replicated correctly to Server 2
```

## Stop Servers

### Linux/macOS:

```bash
./stop_servers.sh
```

### Windows:

Close the server windows or press Ctrl+C in each

### Manual:

Press Ctrl+C in each server terminal

## Common Issues

### "No servers found!"

**Solution:** Make sure servers are running. Check with:
```bash
ps aux | grep server.py    # Linux/macOS
tasklist | findstr python  # Windows
```

### "Address already in use"

**Solution:** A server is already running on that port. Stop it first:
```bash
./stop_servers.sh
```

### Import errors

**Solution:** Make sure all files are in the same directory:
```bash
ls *.py
# Should show: server.py, client.py, admin.py, config.py, distributed.py
```

## Next Steps

- Read [README.md](README.md) for detailed architecture
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for network deployment
- Explore the code to understand distributed algorithms
- Try adding more servers (edit `servers.json`)

## Architecture Overview

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  Server 1   │◄───────►│  Server 2   │◄───────►│  Server 3   │
│  (Kampala)  │         │  (Mbarara)  │         │   (Gulu)    │
└──────▲──────┘         └──────▲──────┘         └──────▲──────┘
       │                       │                        │
       │         ┌─────────────┴────────────┐          │
       │         │                          │          │
       └─────────┤         Client           ├──────────┘
                 │  (Auto-discovers &       │
                 │   connects to nearest)   │
                 └──────────────────────────┘
```

## Key Features You're Using

✓ **Peer-to-peer replication** - All servers have full data  
✓ **Automatic failover** - Client switches if server fails  
✓ **Vector clocks** - Tracks causality of operations  
✓ **2-Phase Commit** - Ensures atomic replication  
✓ **Bully Election** - Elects coordinator automatically  
✓ **Berkeley Clock Sync** - Synchronizes server clocks  
✓ **Anti-entropy** - Gossip protocol fixes inconsistencies  
✓ **Client-centric consistency** - Read-your-writes, monotonic reads/writes  

## Example Session

```bash
# Terminal 1: Start servers
./start_servers.sh

# Terminal 2: Run client
python client.py

# In client:
1. Register new account
   Phone: 256700111222
   PIN: 1234

4. Deposit money
   Amount: 100000

3. Check balance
   ✓ Balance: UGX 100,000.00

6. Switch server
   Select: 2 (MoMo-Mbarara)

3. Check balance again
   ✓ Balance: UGX 100,000.00  # Same data!

5. Withdraw money
   Amount: 25000
   ✓ New balance: UGX 75,000.00

# Terminal 3: Check consistency
python admin.py sync
# ✓ All accounts are consistent across servers!
```

## Troubleshooting Commands

```bash
# Check if servers are running
python admin.py status

# Test the system
python admin.py test

# Check replication
python admin.py sync

# View database
sqlite3 data/server_1.db "SELECT * FROM accounts;"

# Check logs (if redirected)
tail -f logs/server1.log
```

---

**Congratulations!** You now have a fully functional distributed mobile money system running. Explore the code to learn about distributed systems concepts in action!
