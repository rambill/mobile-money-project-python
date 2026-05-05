# 📱 Mobile Phone as Client - Setup Guide

## Overview

You can use your mobile phone as a client in 3 ways:

1. **Termux (Android)** - Run Python directly on phone ⭐ RECOMMENDED
2. **Web Interface** - Access via mobile browser
3. **USSD-style App** - Native mobile app

---

## Option 1: Termux (Android) ⭐ RECOMMENDED

### What is Termux?

Termux is a Linux terminal emulator for Android. You can run Python scripts directly on your phone!

### Step-by-Step Setup

#### Step 1: Install Termux

1. Open **Google Play Store** or **F-Droid**
2. Search for **"Termux"**
3. Install Termux
4. Open Termux

#### Step 2: Install Python

```bash
# In Termux, run:
pkg update
pkg upgrade
pkg install python
```

#### Step 3: Transfer Client Files

**Method A: Using Git (if you have GitHub)**
```bash
# In Termux:
pkg install git
git clone https://github.com/your-repo/mobile-money.git
cd mobile-money
```

**Method B: Manual Transfer**
```bash
# 1. Copy these files to your phone:
#    - client.py
#    - config.py
#    - distributed.py
#    - servers.json

# 2. In Termux, navigate to files:
cd /storage/emulated/0/Download
# Or wherever you saved the files

# 3. Copy to Termux home:
cp client.py config.py distri buted.py servers.json ~/
cd ~
```

#### Step 4: Run Client

```bash
# In Termux:
python client.py

# You should see:
# Discovering servers...
# Found 3 server(s):
#   1. MoMo-Kampala - 0.5ms
#   2. MoMo-Mbarara - 1.2ms
#   3. MoMo-Gulu - 2.3ms
# 
# Connected to: MoMo-Kampala
```

**That's it! Your phone is now a client!** 🎉

---

## Option 2: Web Interface (Any Phone)

I can create a web interface that works on any phone browser.

### Features

- Access via mobile browser (Chrome, Safari, etc.)
- No app installation needed
- Works on Android and iOS
- Touch-friendly interface

### Setup

I'll create:
1. **`web_server.py`** - Flask web server
2. **`templates/mobile.html`** - Mobile-friendly interface
3. **`static/mobile.css`** - Mobile styling

**Would you like me to create this?** Let me know!

---

## Option 3: Native Mobile App

For a full mobile app experience, you'd need:

### Android App (Java/Kotlin)
- Native Android app
- USSD-style interface
- Offline support

### iOS App (Swift)
- Native iOS app
- Touch ID/Face ID support

**This requires mobile app development. Would you like me to create a simple Android app?**

---

## Comparison

| Option | Pros | Cons | Setup Time |
|--------|------|------|------------|
| **Termux** | Full Python, No coding needed | Android only | 5 minutes |
| **Web Interface** | Works on any phone | Needs web server | 10 minutes |
| **Native App** | Best UX, Offline support | Requires app development | Hours/Days |

---

## Recommended: Termux Setup

### Why Termux?

✅ **No coding needed** - Use existing `client.py`  
✅ **Full functionality** - All features work  
✅ **Quick setup** - 5 minutes  
✅ **Free** - No cost  
✅ **Works offline** - No internet needed (just local network)  

### Detailed Termux Instructions

#### 1. Install Termux

**From Google Play Store:**
- Search "Termux"
- Install (Free)

**From F-Droid (Recommended):**
- Go to https://f-droid.org
- Search "Termux"
- Install

#### 2. Setup Python Environment

```bash
# Open Termux and run these commands:

# Update packages
pkg update && pkg upgrade

# Install Python
pkg install python

# Verify installation
python --version
# Should show: Python 3.x.x
```

#### 3. Transfer Files to Phone

**Option A: Using USB Cable**
```bash
# 1. Connect phone to PC via USB
# 2. Copy these files to phone's Download folder:
#    - client.py
#    - config.py
#    - distributed.py
#    - servers.json

# 3. In Termux:
termux-setup-storage  # Grant storage permission
cd ~/storage/downloads
cp client.py config.py distributed.py servers.json ~/
cd ~
```

**Option B: Using Cloud (Google Drive, Dropbox)**
```bash
# 1. Upload files to Google Drive from PC
# 2. Download files on phone
# 3. In Termux:
termux-setup-storage
cd ~/storage/downloads
cp *.py ~/
cp servers.json ~/
cd ~
```

**Option C: Using Termux Editor**
```bash
# Create files directly in Termux:
nano client.py
# Paste content, Ctrl+X to save

nano config.py
# Paste content, Ctrl+X to save

nano distributed.py
# Paste content, Ctrl+X to save

nano servers.json
# Paste content, Ctrl+X to save
```

#### 4. Run Client

```bash
# Make sure you're on same WiFi network as servers
python client.py
```

#### 5. Use Mobile Money

```bash
# The interface works the same:
# 1. Register new account
# 2. Login
# 3. Check balance
# 4. Deposit money
# 5. Withdraw money
# 6. Transfer money
# 7. Switch server
# 8. Show server status
# 0. Exit
```

---

## Network Requirements

### Important: Phone Must Be on Same Network

Your phone needs to connect to the same network as the servers:

**Option A: Same WiFi**
```
Phone → WiFi → Router → Servers
```

**Option B: Mobile Hotspot**
```
Phone (Hotspot) → Servers connect to phone's hotspot
```

**Option C: VPN**
```
Phone → VPN → Server Network
```

### Check Network Connectivity

```bash
# In Termux, ping servers:
ping 10.29.42.224  # Server 1
ping 10.29.42.65   # Server 2
ping 10.29.42.17   # Server 3

# If ping works, client will work!
```

---

## Troubleshooting

### "Command not found: python"

**Solution:**
```bash
pkg install python
```

### "Permission denied"

**Solution:**
```bash
termux-setup-storage
# Grant storage permission in popup
```

### "No servers found"

**Solution:**
```bash
# Check network:
ping 10.29.42.224

# Check servers.json exists:
ls -la servers.json

# Check WiFi connection:
# Make sure phone is on same network as servers
```

### "Module not found: config"

**Solution:**
```bash
# Make sure all files are in same directory:
ls -la
# Should show: client.py, config.py, distributed.py, servers.json

# If not, copy them:
cp ~/storage/downloads/*.py ~/
```

---

## Alternative: Create Web Interface

If Termux doesn't work for you, I can create a web interface:

### Features

- Mobile-friendly design
- Touch-optimized buttons
- Works on any phone (Android/iOS)
- No app installation needed

### What I'll Create

1. **`web_server.py`** - Flask web server
2. **`templates/mobile.html`** - Mobile interface
3. **`static/mobile.css`** - Mobile styling
4. **`static/mobile.js`** - Mobile interactions

### How It Works

```
Phone Browser → http://server-ip:8000 → Web Interface → Servers
```

**Would you like me to create this web interface?**

---

## Summary

### Recommended: Termux

**Steps:**
1. Install Termux from Play Store
2. Install Python: `pkg install python`
3. Copy files to phone
4. Run: `python client.py`
5. Done! 🎉

**Time:** 5-10 minutes  
**Cost:** Free  
**Works:** Android only  

### Alternative: Web Interface

**Steps:**
1. I create web interface
2. Run web server on PC
3. Access from phone browser
4. Done! 🎉

**Time:** 10 minutes (for me to create)  
**Cost:** Free  
**Works:** Any phone (Android/iOS)  

---

## Which Option Do You Want?

1. **Termux** - I'll help you set it up (5 minutes)
2. **Web Interface** - I'll create it for you (10 minutes)
3. **Both** - Best of both worlds!

Let me know and I'll help you get started! 📱✨
