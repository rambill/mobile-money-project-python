# ⚡ Quick Start Guide - Distributed Mobile Money System

**Get up and running in 5 minutes!**

---

## 🚀 Quick Setup

### 1. Start Servers (Pick Your Servers)

```bash
# Start Server 1 (Kampala):
python server.py 1

# Start Server 2 (Mbarara):
python server.py 2

# Start Server 3 (Gulu):
python server.py 3

# ... or start all 10 servers
```

### 2. Sync Data (After All Servers Started)

```bash
# If servers on SAME machine:
python peer_sync.py

# If servers on DIFFERENT machines:
python network_sync.py
```

### 3. Connect Client

```bash
# Terminal client:
python client.py

# Web interface (for mobile phones):
python web_client.py
# Then open http://<your-ip>:8000 on phone
```

**That's it! You're ready to go!** 🎉

---

## 📱 Client Options

### Option 1: Terminal Client (PC)

```bash
python client.py

# Features:
# - Register account
# - Login
# - Check balance
# - Deposit money
# - Withdraw money
# - Transfer money
# - Switch servers
```

### Option 2: Mobile Phone (Termux - Android)

```bash
# On Android phone:
# 1. Install Termux from Play Store
# 2. In Termux:
pkg install python
# 3. Copy files to phone
# 4. Run:
python client.py
```

### Option 3: Web Interface (Any Phone)

```bash
# On PC:
pip install flask
python web_client.py

# On phone browser:
# Open: http://<your-pc-ip>:8000
```

---

## 🎯 Common Tasks

### Register New Account

```bash
# 1. Start client:
python client.py

# 2. Choose option 1 (Register)
# 3. Enter phone number: 0759016809
# 4. Enter PIN: 1234
# 5. Confirm PIN: 1234
# 6. Done! Account created
```

### Check Balance

```bash
# 1. Login (option 2)
# 2. Choose option 3 (Check Balance)
# 3. See your balance
```

### Deposit Money

```bash
# 1. Login
# 2. Choose option 4 (Deposit)
# 3. Enter amount: 50000
# 4. Done! Money deposited
```

### Transfer Money

```bash
# 1. Login
# 2. Choose option 6 (Transfer)
# 3. Enter recipient phone: 0759882820
# 4. Enter amount: 10000
# 5. Done! Money transferred
```

---

## 🔧 Troubleshooting

### "No servers found"

**Solution:**
```bash
# 1. Check servers are running:
# Look for "Ready!" message

# 2. Check firewall:
# Windows: Allow UDP ports 6001-6010, 6101-6110, 5999

# 3. Check network:
# Make sure client and servers on same network
```

### "Invalid PIN"

**Solution:**
```bash
# Sync databases:
python peer_sync.py

# This ensures all servers have all accounts
```

### "Servers have different data"

**Solution:**
```bash
# 1. Check differences:
python compare_databases.py

# 2. Sync all servers:
# If same machine:
python peer_sync.py

# If different machines (servers must be running):
python network_sync.py

# 3. Verify sync worked:
python compare_databases.py
```

---

## 📊 Server Management

### Start All Servers (Windows)

Create `start_all.bat`:
```batch
@echo off
start "Kampala" python server.py 1
start "Mbarara" python server.py 2
start "Gulu" python server.py 3
start "Kasese" python server.py 4
start "Kabale" python server.py 5
start "Mbale" python server.py 6
start "Jinja" python server.py 7
start "Rukungiri" python server.py 8
start "Fort Portal" python server.py 9
start "Arua" python server.py 10
```

Then run:
```bash
start_all.bat
```

### Stop All Servers

Press `Ctrl+C` in each server window

### Check Server Status

```bash
# In client:
python client.py
# Choose option 8 (Show server status)
```

---

## 🌐 Network Setup

### Firewall Rules (Windows)

```powershell
# Allow RPC ports (6001-6010):
New-NetFirewallRule -DisplayName "Mobile Money RPC" -Direction Inbound -Protocol UDP -LocalPort 6001-6010 -Action Allow

# Allow replication ports (6101-6110):
New-NetFirewallRule -DisplayName "Mobile Money Replication" -Direction Inbound -Protocol UDP -LocalPort 6101-6110 -Action Allow

# Allow discovery port (5999):
New-NetFirewallRule -DisplayName "Mobile Money Discovery" -Direction Inbound -Protocol UDP -LocalPort 5999 -Action Allow
```

### Find Your IP Address

```bash
# Windows:
ipconfig

# Linux/Mac:
ifconfig

# Look for IPv4 address (e.g., 10.29.42.224)
```

---

## 📁 File Structure

```
mobile-money/
├── server.py              # Main server
├── client.py              # Terminal client
├── web_client.py          # Web interface
├── config.py              # Configuration
├── distributed.py         # Distributed algorithms
├── servers.json           # Server list
├── mobile.sql             # Database schema
├── peer_sync.py           # Sync tool
├── compare_databases.py   # Compare tool
├── data/                  # Databases
│   ├── server_1.db
│   ├── server_2.db
│   └── ...
└── templates/             # Web templates
    └── mobile.html
```

---

## 🎓 Key Concepts

### Peer-to-Peer
- All servers are equal (no master)
- Each server replicates to all others
- Any server can fail without affecting system

### Eventual Consistency
- Changes replicate asynchronously
- All servers eventually have same data
- Use `peer_sync.py` to force sync

### Vector Clocks
- Track causality of updates
- Detect concurrent updates
- Enable conflict resolution

### Last-Writer-Wins
- When conflict detected, newest update wins
- Based on physical timestamp
- Simple and effective

---

## 📞 Quick Commands

```bash
# Start server:
python server.py <id>

# Start client:
python client.py

# Sync databases (same machine):
python peer_sync.py

# Sync databases (different machines):
python network_sync.py

# Compare databases:
python compare_databases.py

# Web interface:
python web_client.py
```

---

## 🎯 Typical Workflow

### First Time Setup

```bash
# 1. Start servers:
python server.py 1
python server.py 2
python server.py 3

# 2. Wait 10 seconds for servers to initialize

# 3. Sync data:
python peer_sync.py

# 4. Connect client:
python client.py

# 5. Register account and start using!
```

### Daily Use

```bash
# 1. Start servers (if not running):
python server.py 1
python server.py 2
python server.py 3

# 2. Connect client:
python client.py

# 3. Use mobile money!
```

### Adding New Server

```bash
# 1. Update servers.json:
# Add new server entry

# 2. Update config.py:
# Add new server to SERVERS list

# 3. Start new server:
python server.py <new_id>

# 4. Sync data:
python peer_sync.py

# 5. Done! New server has all data
```

---

## 💡 Tips & Tricks

### Tip 1: Always Sync After Changes
```bash
# After adding accounts on one server:
python peer_sync.py
# Ensures all servers have the account
```

### Tip 2: Check Differences Regularly
```bash
# See if servers are in sync:
python compare_databases.py
```

### Tip 3: Use Web Interface for Mobile
```bash
# Easier than Termux:
python web_client.py
# Access from any phone browser
```

### Tip 4: Start Servers in Order
```bash
# Start Server 1 first, then others:
python server.py 1  # Wait 5 seconds
python server.py 2  # Wait 5 seconds
python server.py 3  # Wait 5 seconds
# Then sync:
python peer_sync.py
```

### Tip 5: Keep Servers Running
```bash
# Servers should run continuously
# Don't restart unless necessary
# If restart needed, sync after:
python peer_sync.py
```

---

## 🔍 Verification

### Check Everything Works

```bash
# 1. Start 2 servers:
python server.py 1
python server.py 2

# 2. Sync:
python peer_sync.py

# 3. Register account on Server 1:
python client.py
# Register: 0759016809, PIN: 1234

# 4. Switch to Server 2:
# Option 7 (Switch server)
# Choose Server 2

# 5. Login with same account:
# Option 2 (Login)
# Phone: 0759016809, PIN: 1234

# 6. If login works, system is working! ✅
```

---

## 📚 More Information

- **`PROJECT_STATUS.md`** - Current system status
- **`ALL_SERVERS.md`** - All 10 servers documentation
- **`ARCHITECTURE.md`** - System architecture
- **`MOBILE_CLIENT_SETUP.md`** - Mobile phone setup
- **`WEB_CLIENT_SETUP.md`** - Web interface setup

---

## 🎉 You're Ready!

**Quick recap:**
1. Start servers: `python server.py 1`
2. Sync data: `python peer_sync.py`
3. Connect client: `python client.py`
4. Use mobile money! 💰

**Need help?** Check the documentation files above!

---

**Happy banking!** 🏦✨
