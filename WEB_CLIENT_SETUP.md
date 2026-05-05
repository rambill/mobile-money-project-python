# 🌐 Web Client Setup - Access from Any Phone!

## Overview

The web client allows you to access Mobile Money from **any phone browser** (Android, iOS, etc.)!

---

## Quick Setup (5 Minutes)

### Step 1: Install Flask

```bash
# On your PC (where servers are running):
pip install flask
```

### Step 2: Start Web Server

```bash
python web_client.py

# You'll see:
# ============================================================
# MOBILE MONEY WEB CLIENT
# ============================================================
# 
# Starting web server...
# 
# Access from your phone:
#   http://<your-pc-ip>:8000
# 
# Example:
#   http://10.29.42.224:8000
# 
# ============================================================
```

### Step 3: Access from Phone

1. **Connect phone to same WiFi** as PC
2. **Open browser** on phone (Chrome, Safari, etc.)
3. **Go to:** `http://<your-pc-ip>:8000`
   - Example: `http://10.29.42.224:8000`
4. **Done!** You'll see the mobile interface

---

## Features

### ✅ Mobile-Friendly Interface

- Touch-optimized buttons
- Large, easy-to-tap controls
- Responsive design
- Works on any screen size

### ✅ Full Functionality

- Register new account
- Login
- Check balance
- Deposit money
- Withdraw money
- Transfer money
- Switch servers
- Logout

### ✅ Works on Any Phone

- Android (Chrome, Samsung Browser, etc.)
- iOS (Safari)
- Any phone with a browser!

### ✅ No App Installation

- Just open browser
- No Play Store/App Store needed
- Works immediately

---

## How to Find Your PC IP Address

### Windows

```bash
ipconfig

# Look for "IPv4 Address" under your WiFi adapter
# Example: 10.29.42.224
```

### Linux/Mac

```bash
ifconfig

# Look for "inet" under your WiFi interface
# Example: 10.29.42.224
```

---

## Usage

### 1. Register New Account

```
1. Open http://<your-pc-ip>:8000 on phone
2. Click "Register New Account"
3. Enter phone number (e.g., 0759016809)
4. Enter 4-digit PIN
5. Confirm PIN
6. Select server
7. Click "Create Account"
8. Done! You're logged in
```

### 2. Login

```
1. Open http://<your-pc-ip>:8000 on phone
2. Enter phone number
3. Enter PIN
4. Select server
5. Click "Login"
6. Done! You see your balance
```

### 3. Deposit Money

```
1. From main screen, click "Deposit"
2. Enter amount
3. Click "Deposit"
4. Done! Balance updated
```

### 4. Withdraw Money

```
1. From main screen, click "Withdraw"
2. Enter amount
3. Click "Withdraw"
4. Done! Balance updated
```

### 5. Transfer Money

```
1. From main screen, click "Transfer"
2. Enter recipient phone number
3. Enter amount
4. Click "Transfer"
5. Done! Money transferred
```

---

## Screenshots (What You'll See)

### Login Screen
```
┌─────────────────────────┐
│   📱 Mobile Money       │
│                         │
│  Phone Number:          │
│  [0759016809        ]   │
│                         │
│  PIN:                   │
│  [****              ]   │
│                         │
│  Server:                │
│  [Kampala ▼    ]   │
│                         │
│  [     Login        ]   │
│  [ Register Account ]   │
└─────────────────────────┘
```

### Main Screen
```
┌─────────────────────────┐
│   💰 My Account         │
│                         │
│  Connected: Kampala│
│  Phone: 0759016809      │
│                         │
│  ┌───────────────────┐  │
│  │ Current Balance   │  │
│  │  UGX 54,000      │  │
│  └───────────────────┘  │
│                         │
│  [💵 Deposit] [💸 Withdraw]│
│  [↔️ Transfer] [🔄 Refresh]│
│                         │
│  [     Logout       ]   │
└─────────────────────────┘
```

---

## Advantages

### vs Termux

| Feature | Web Client | Termux |
|---------|------------|--------|
| **Setup** | 5 minutes | 10 minutes |
| **Works on** | Any phone | Android only |
| **Interface** | Touch-friendly | Terminal |
| **Installation** | None (browser) | App install needed |

### vs Native App

| Feature | Web Client | Native App |
|---------|------------|------------|
| **Development** | Done! | Weeks/months |
| **Updates** | Instant | App store approval |
| **Installation** | None | App store |
| **Cost** | Free | Development cost |

---

## Troubleshooting

### Can't Access from Phone

**Check 1: Same WiFi?**
```
Phone and PC must be on same WiFi network
```

**Check 2: Firewall?**
```bash
# Windows: Allow port 8000
# Firewall → Inbound Rules → New Rule → Port → TCP 8000
```

**Check 3: Correct IP?**
```bash
# On PC:
ipconfig  # Windows
ifconfig  # Linux/Mac

# Use the IPv4 address shown
```

**Check 4: Server running?**
```bash
# Make sure web_client.py is running
python web_client.py
```

### "No servers found"

**Cause:** Mobile money servers not running

**Solution:**
```bash
# Start servers:
python server.py 1
python server.py 2
python server.py 3
```

### "Request timeout"

**Cause:** Servers not reachable

**Solution:**
```bash
# Check servers are running
# Check servers.json has correct IPs
# Check firewall allows UDP ports 6001, 6002, 6003
```

---

## Advanced: Access from Internet

### Using ngrok (Expose to Internet)

```bash
# Install ngrok
# Download from: https://ngrok.com

# Run web client
python web_client.py

# In another terminal:
ngrok http 8000

# You'll get a public URL:
# https://abc123.ngrok.io

# Access from anywhere:
# Open https://abc123.ngrok.io on any phone
```

**Warning:** Only use for testing! Not secure for production.

---

## Comparison: All Options

| Option | Setup | Works On | Interface | Best For |
|--------|-------|----------|-----------|----------|
| **Termux** | 10 min | Android | Terminal | Power users |
| **Web Client** | 5 min | Any phone | Touch UI | Everyone |
| **Native App** | Weeks | Specific OS | Native | Production |

---

## Summary

**Setup:**
```bash
pip install flask
python web_client.py
```

**Access:**
```
http://<your-pc-ip>:8000
```

**Features:**
- Mobile-friendly interface
- Works on any phone
- No app installation
- Full functionality

---

**Access Mobile Money from any phone browser!** 🌐📱

**No app installation needed!** ✨
