# Deployment Guide - Distributed Mobile Money System

This guide covers deploying the mobile money system across multiple machines in a real network environment.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Network Setup](#network-setup)
3. [Configuration](#configuration)
4. [Deployment Modes](#deployment-modes)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Software Requirements
- Python 3.8 or higher
- Network connectivity between all machines
- Firewall configured to allow UDP traffic

### System Requirements (per server)
- CPU: 1+ cores
- RAM: 512MB minimum
- Disk: 100MB for database and logs
- Network: UDP ports accessible

## Network Setup

### Port Requirements

Each server requires **2 UDP ports**:
- **RPC Port** (600X): Client requests
- **Replication Port** (610X): Peer-to-peer communication

Additionally, all servers use:
- **Discovery Port** (5999): Server discovery broadcasts

### Firewall Configuration

**Linux (ufw):**
```bash
sudo ufw allow 6001:6010/udp
sudo ufw allow 5999/udp
```

**Windows Firewall:**
```powershell
New-NetFirewallRule -DisplayName "Mobile Money RPC" -Direction Inbound -Protocol UDP -LocalPort 6001-6010 -Action Allow
New-NetFirewallRule -DisplayName "Mobile Money Discovery" -Direction Inbound -Protocol UDP -LocalPort 5999 -Action Allow
```

**macOS:**
```bash
# macOS firewall typically allows outbound by default
# For inbound, add rules in System Preferences > Security & Privacy > Firewall
```

## Configuration

### 1. Edit servers.json

Create or edit `servers.json` with your actual server IP addresses:

```json
{
  "servers": [
    {
      "id": 1,
      "name": "Server-1",
      "region": "Data Center A",
      "host": "192.168.1.100",
      "port": 6001,
      "rep_port": 6101,
      "active": true
    },
    {
      "id": 2,
      "name": "Server-2",
      "region": "Data Center B",
      "host": "10.0.0.50",
      "port": 6001,
      "rep_port": 6101,
      "active": true
    },
    {
      "id": 3,
      "name": "Server-3",
      "region": "Data Center C",
      "host": "172.16.0.25",
      "port": 6001,
      "rep_port": 6101,
      "active": true
    }
  ]
}
```

**Important:** 
- Use actual IP addresses, not 127.0.0.1 for network deployment
- All servers must have the **same** `servers.json` file
- Ensure `host` is the IP address where the server will bind

### 2. Copy Files to Each Machine

Copy the entire project to each server machine:

```bash
# On your development machine
tar -czf mobile-money-system.tar.gz *.py *.sql *.json *.md

# Copy to each server
scp mobile-money-system.tar.gz user@192.168.1.100:~/
scp mobile-money-system.tar.gz user@10.0.0.50:~/
scp mobile-money-system.tar.gz user@172.16.0.25:~/

# On each server, extract
tar -xzf mobile-money-system.tar.gz
```

## Deployment Modes

### Mode 1: Localhost (Development)

For testing on a single machine:

**Linux/macOS:**
```bash
chmod +x start_servers.sh
./start_servers.sh
```

**Windows:**
```cmd
start_servers.bat
```

**Or manually:**
```bash
python server.py 1
python server.py 2
python server.py 3
```

### Mode 2: Network Deployment (Production)

#### Step 1: Start Servers

On **Machine A** (192.168.1.100):
```bash
python server.py 1
```

On **Machine B** (10.0.0.50):
```bash
python server.py 2
```

On **Machine C** (172.16.0.25):
```bash
python server.py 3
```

#### Step 2: Verify Connectivity

On any machine, run:
```bash
python admin.py status
```

You should see all 3 servers listed.

#### Step 3: Run Client

From any machine with network access:
```bash
python client.py
```

The client will automatically discover and connect to the nearest server.

### Mode 3: Hybrid (Some Local, Some Remote)

You can mix localhost and network servers:

```json
{
  "servers": [
    {"id": 1, "host": "127.0.0.1", "port": 6001, "rep_port": 6101, "active": true},
    {"id": 2, "host": "192.168.1.100", "port": 6001, "rep_port": 6101, "active": true},
    {"id": 3, "host": "10.0.0.50", "port": 6001, "rep_port": 6101, "active": true}
  ]
}
```

## Testing

### 1. Connectivity Test

Test UDP connectivity between servers:

```bash
# On Server 1, test connection to Server 2
nc -u 10.0.0.50 6001
```

### 2. Discovery Test

```bash
# Should list all running servers
python admin.py status
```

### 3. Integration Tests

```bash
# Run automated tests
python admin.py test
```

### 4. Consistency Check

```bash
# Verify replication is working
python admin.py sync
```

### 5. Manual Client Test

```bash
python client.py
# Try: Register → Deposit → Check Balance on different server
```

## Monitoring

### Server Logs

Each server outputs logs to stdout. Redirect to file:

```bash
python server.py 1 > logs/server1.log 2>&1 &
```

### Database Inspection

```bash
sqlite3 data/server_1.db
sqlite> SELECT * FROM accounts;
sqlite> SELECT * FROM transactions;
sqlite> .quit
```

### Real-time Monitoring

```bash
# Watch server status
watch -n 5 'python admin.py status'
```

## Troubleshooting

### Problem: Client can't discover servers

**Symptoms:** "No servers found!"

**Solutions:**
1. Check servers are running: `ps aux | grep server.py`
2. Verify firewall allows UDP 5999
3. Check network connectivity: `ping <server_ip>`
4. Ensure broadcast is enabled on network

### Problem: Replication fails

**Symptoms:** Consistency check shows mismatches

**Solutions:**
1. Verify all servers have same `servers.json`
2. Check replication ports (610X) are open
3. Check network latency: `ping -c 10 <server_ip>`
4. Increase `TWO_PC_TIMEOUT_SEC` in `config.py`

### Problem: Election loops

**Symptoms:** Servers keep re-electing coordinator

**Solutions:**
1. Ensure server IDs are unique
2. Check `COORDINATOR_TIMEOUT_SEC` isn't too low
3. Verify network stability (no packet loss)

### Problem: Lock timeouts

**Symptoms:** "Lock timeout" errors

**Solutions:**
1. Increase `LOCK_TIMEOUT_SEC` in `config.py`
2. Check coordinator is alive: `python admin.py status`
3. Verify network latency is acceptable

### Problem: Clock drift warnings

**Symptoms:** "Clock drift too large" messages

**Solutions:**
1. Increase `MAX_CLOCK_DRIFT_SEC` in `config.py`
2. Use NTP on all machines: `sudo ntpdate pool.ntp.org`
3. Check network latency between servers

## Performance Tuning

### For High-Latency Networks

```python
# In config.py
UDP_TIMEOUT_SEC = 5.0              # Increase from 2.0
TWO_PC_TIMEOUT_SEC = 5.0           # Increase from 3.0
LOCK_REQUEST_TIMEOUT_SEC = 5.0     # Increase from 3.0
```

### For Low-Bandwidth Networks

```python
# In config.py
GOSSIP_INTERVAL_SEC = 120.0        # Decrease gossip frequency
CLOCK_SYNC_INTERVAL_SEC = 30.0     # Decrease sync frequency
```

### For High-Traffic Scenarios

```python
# In config.py
SERVER_CACHE_TTL_SEC = 30.0        # Increase cache duration
CLIENT_CACHE_TTL_SEC = 10.0        # Increase cache duration
```

## Security Considerations

### 1. Network Security

- Use VPN or private network for server communication
- Implement firewall rules to restrict access
- Consider encrypting UDP packets (add TLS layer)

### 2. Authentication

- Current system uses simple PIN (4 digits)
- For production, implement:
  - Hashed PINs (bcrypt/scrypt)
  - Session tokens
  - Rate limiting

### 3. Data Security

- Database files are unencrypted
- For production, use SQLite encryption extension
- Implement audit logging

## Scaling

### Adding More Servers

1. Edit `servers.json` to add new server entry
2. Copy updated `servers.json` to all machines
3. Start new server: `python server.py <new_id>`
4. Server will auto-sync state from peers

### Removing Servers

1. Stop the server: `kill <pid>`
2. Edit `servers.json` and set `"active": false`
3. Copy updated config to all machines
4. Remaining servers will continue operating

## Backup and Recovery

### Database Backup

```bash
# Backup all server databases
tar -czf backup-$(date +%Y%m%d).tar.gz data/
```

### WAL Recovery

On server crash, WAL automatically recovers on restart:

```bash
# Server will log: "Found X orphaned transactions, aborting..."
python server.py 1
```

### State Sync

If a server is behind, it will auto-sync on startup:

```bash
# Server will log: "State sync from peers..."
python server.py 1
```

## Production Checklist

- [ ] All servers have same `servers.json`
- [ ] Firewall rules configured
- [ ] Network connectivity tested
- [ ] NTP synchronized across machines
- [ ] Monitoring/logging configured
- [ ] Backup strategy in place
- [ ] Security hardening applied
- [ ] Integration tests passing
- [ ] Consistency check passing
- [ ] Load testing completed

---

For questions or issues, refer to the main [README.md](README.md) or check the troubleshooting section above.
