# Distributed Mobile Money System

A distributed mobile money service built on a peer-to-peer replica architecture using UDP. Designed for low-bandwidth environments (GPRS/EDGE), it supports 10 geographically distributed server nodes across Uganda with automatic client-to-server routing based on latency.

## Distributed Systems Features

| Feature | Implementation | Description |
|---|---|---|
| **Architecture** | Peer-to-peer replicated | 10 full-replica servers, no single master, any server serves any client |
| **RPC** | Custom UDP protocol | `REQ\|id\|CMD\|args` / `RES\|id\|OK\|msg\|bal\|vc` — packets ≤ 512 bytes |
| **Naming** | Flat + Discovery | Server IDs, phone-based account keys, UDP broadcast discovery on port 5999 |
| **Synchronization — Clocks** | Vector clocks + Berkeley | Vector clocks for causal ordering; Berkeley algorithm for physical clock sync |
| **Synchronization — Mutual Exclusion** | Coordinator-based locks | Per-account distributed locking via elected coordinator before every write |
| **Caching** | Client + Server TTL | Client-side (5s TTL) and server-side (10s TTL) with write-through invalidation |
| **Replication** | Active + 2PC | Writes replicate to all peers via True 2-Phase Commit with Write-Ahead Log |
| **Consistency — Ordering** | Causal (vector clocks) | Every write tagged with vector clock; causal comparison for state sync |
| **Consistency — Client-Centric** | 4 models | Read-your-writes, Monotonic reads, Monotonic writes, Writes-follow-reads |
| **Conflict Resolution** | Last-Writer-Wins (LWW) | Concurrent vector clocks resolved by physical timestamp + server ID tiebreaker |
| **Fault Tolerance** | 2PC + Rollback + WAL | PREPARE/VOTE/COMMIT/ABORT; WAL crash recovery; rollback on replication failure |
| **Availability** | Auto-failover | Client auto-switches to next server on failure; state sync on server recovery |
| **Reliability** | Exactly-once delivery | Sequence numbers + replication log prevent duplicate application |
| **Election** | Bully algorithm | Highest-ID alive server becomes coordinator; heartbeat-based failure detection |
| **Anti-Entropy** | Gossip + Merkle trees | Periodic Merkle-hash comparison with random peer; sync only differing accounts |

## Files

| File | Purpose |
|---|---|
| `server.py` | Server process — handles client RPC, replication, and all distributed algorithms |
| `client.py` | Client program — discovers nearest server, manages sessions, tracks consistency |
| `config.py` | Server list, network ports, and all feature configuration constants |
| `distributed.py` | Distributed algorithm implementations (Election, Clock Sync, Locks, 2PC, LWW, Gossip) |
| `mobile.sql` | Database schema — accounts, transactions, replication log, server registry |
| `admin.py` | Admin console — server status, replication consistency check, integration tests |
| `data/` | SQLite databases (`server_N.db`) and Write-Ahead Logs (`wal/server_N.wal`) |
| `start_servers.sh` / `stop_servers.sh` | Helper scripts to run or stop all servers |

## Requirements

- Python 3.8+ on all machines
- Network connectivity between all server laptops and clients
- Each server laptop must receive UDP traffic on two ports per node

## Quick Start

### Mode 1: Same Machine (Localhost Mode)

On different terminals, run each server with a unique ID:

```bash
python server.py 1    # Terminal 1 — MoMo-Kampala  (127.0.0.1:6001)
python server.py 2    # Terminal 2 — MoMo-Mbarara  (127.0.0.1:6002)
python server.py 3    # Terminal 3 — MoMo-Gulu     (127.0.0.1:6003)
```

Then in a 4th terminal, run the client:

```bash
python client.py      # Auto-discovers servers and connects
```

### Mode 2: Separate Machines (Network Mode) ⭐ **NEW**

For deployment across different machines with real IP addresses:

1. **Edit `servers.json`** with your server IP addresses:

```json
{
  "servers": [
    {"id":1, "name":"MoMo-Server-1", "region":"DC-A", "host":"192.168.1.100", "port":6001, "rep_port":6101, "active":true},
    {"id":2, "name":"MoMo-Server-2", "region":"DC-B", "host":"10.0.0.50", "port":6001, "rep_port":6101, "active":true},
    {"id":3, "name":"MoMo-Server-3", "region":"DC-C", "host":"172.16.0.25", "port":6001, "rep_port":6101, "active":true}
  ]
}
```

2. **Copy the project** to each machine

3. **Start servers** on each machine with its ID:

```bash
# On Machine A (192.168.1.100)
python server.py 1

# On Machine B (10.0.0.50)
python server.py 2

# On Machine C (172.16.0.25)
python server.py 3
```

4. **Run client** from any machine with network access:

```bash
python client.py    # Auto-detects servers across network
```

**Complete setup instructions:** See [DEPLOYMENT.md](DEPLOYMENT.md)

### Server Startup Sequence

On startup, each server will:
1. Load the SQLite database and schema
2. Start RPC, Replication, and Discovery services
3. Run a **Bully Election** to elect a coordinator
4. Start **Berkeley Clock Sync** (if elected coordinator)
5. Start **Anti-Entropy/Gossip** background thread
6. **State-sync** from peers to catch up on missed data
7. Begin accepting client traffic

### Admin Tools

```bash
python admin.py status    # Live server stats
python admin.py sync      # Check replication consistency
python admin.py test      # Run integration tests
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Server Node                           │
├──────────────┬──────────────────┬───────────────────────────┤
│   RPCServer  │ ReplicationMgr   │  ServerDiscoveryService   │
│  (UDP :600X) │  (UDP :610X)     │  (UDP :5999 broadcast)    │
│              │                  │                           │
│  Handles:    │  Routes msgs to: │  Broadcasts load status   │
│  - Client RPC│  - BullyElection │  Responds to DISCOVER     │
│  - Lock/2PC  │  - ClockSync     │                           │
│  - Monotonic │  - LockMgr       │                           │
│    writes    │  - TwoPhaseCommit│                           │
│  - WFR check │  - AntiEntropy   │                           │
├──────────────┴──────────────────┴───────────────────────────┤
│                  DataStore (SQLite)                          │
│  - Vector clocks per account                                │
│  - Replication log (exactly-once)                           │
│  - Account cache with TTL                                   │
└─────────────────────────────────────────────────────────────┘
```

### Write Operation Flow

```
Client → Server:  REQ|id|DEPOSIT|phone|pin|amount|write_vc|read_vc
                     │
                     ├─ Check Monotonic Writes (client write_vc ≤ local VC?)
                     ├─ Check Writes-Follow-Reads (local VC ≥ client read_vc?)
                     ├─ Acquire Distributed Lock (LOCK_REQ → Coordinator)
                     ├─ Apply write locally (SQLite + vector clock increment)
                     ├─ 2PC: PREPARE → all peers
                     │        ← VOTE_YES from all peers
                     │        COMMIT → all peers (they apply the write)
                     ├─ Release Distributed Lock (LOCK_RELEASE → Coordinator)
                     │
Server → Client:  RES|id|OK|message|balance|vector_clock_json
```

### Election & Coordinator Responsibilities

The **Bully Algorithm** elects the highest-ID alive server as coordinator. The coordinator runs:

1. **Berkeley Clock Sync** — queries all peers for their time every 15s, computes average, sends adjustments
2. **Distributed Lock Table** — maintains `{phone → (holder_server, expiry)}`, grants/denies lock requests
3. **Heartbeats** — sends `ELECT_HB` every 5s; if no heartbeat for 12s, peers start a new election

## Configuration

All settings are in `config.py`. Key parameters:

```python
# Election
ELECTION_TIMEOUT_SEC        = 3.0    # Wait for ANSWER before declaring victory
COORDINATOR_HEARTBEAT_SEC   = 5.0    # Heartbeat interval
COORDINATOR_TIMEOUT_SEC     = 12.0   # Trigger re-election if no heartbeat

# Clock Sync (Berkeley)
CLOCK_SYNC_INTERVAL_SEC     = 15.0   # Sync frequency
MAX_CLOCK_DRIFT_SEC         = 5.0    # Ignore outlier responses

# Distributed Locks
LOCK_TIMEOUT_SEC            = 5.0    # Auto-expire to prevent deadlocks
LOCK_REQUEST_TIMEOUT_SEC    = 3.0    # Client wait for grant/deny

# 2-Phase Commit
TWO_PC_ENABLED              = True
TWO_PC_TIMEOUT_SEC          = 3.0    # Vote collection timeout
TWO_PC_WAL_DIR              = "wal"  # Write-Ahead Log directory

# Conflict Resolution
CONFLICT_STRATEGY           = "LWW"  # Last-Writer-Wins

# Anti-Entropy / Gossip
GOSSIP_INTERVAL_SEC         = 60.0   # Gossip frequency
MERKLE_HASH_DEPTH           = 4      # Merkle tree depth

# Consistency Models
READ_YOUR_WRITES            = True
MONOTONIC_READS             = True
MONOTONIC_WRITES            = True
WRITES_FOLLOW_READS         = True
```

## How to Add More Servers

1. Open `config.py`
2. Add a new entry to the `SERVERS` list:
   ```python
   {
       "id":       11,
       "name":     "MoMo-Soroti",
       "region":   "Eastern Uganda",
       "host":     "192.168.1.21",
       "port":     6011,
       "rep_port": 6111,
       "active":   True,
   },
   ```
3. Copy the same `config.py` to all server laptops
4. Run `python server.py 11` on the new laptop
5. The new server will auto-sync state from peers and join the cluster

## Consistency Guarantees

| Model | How Enforced |
|---|---|
| **Read-your-writes** | Client routes reads to last-write server within TTL window |
| **Monotonic reads** | Client prefers last-write server; vector clock comparison |
| **Monotonic writes** | Client sends last-write VC; server rejects if VC > local |
| **Writes-follow-reads** | Client sends last-read VC; server rejects if VC > local |
| **Causal consistency** | Vector clocks on every account; causal comparison during sync |
| **Eventual consistency** | Anti-entropy gossip + replication ensures convergence |

## Fault Tolerance

| Failure | Recovery |
|---|---|
| **Server crash** | On restart: WAL recovery aborts orphaned 2PC transactions; state sync from peers catches up missed data |
| **Coordinator crash** | Peers detect missing heartbeat after 12s → Bully election elects new coordinator |
| **Network partition** | Clients auto-failover to reachable servers; gossip re-syncs when partition heals |
| **Replication failure** | 2PC aborts → local write rolled back → client gets error, can retry |
| **Concurrent writes** | Distributed locks prevent conflicting writes; LWW resolves any remaining races |

## Troubleshooting

- **Client can't reach any server** — verify servers are running and UDP ports are open
- **Replication fails** — check `config.py` is identical on all laptops
- **Election loops** — ensure server IDs are unique and ports don't conflict
- **Clock drift warnings** — check `MAX_CLOCK_DRIFT_SEC` isn't too small for your network latency
- **Lock timeouts** — increase `LOCK_TIMEOUT_SEC` if operations take longer than 5s
- **2PC aborts** — check peer connectivity; increase `TWO_PC_TIMEOUT_SEC` on slow networks

---

This system implements all core distributed systems concepts: architecture, RPC, naming, synchronization (vector clocks, Berkeley clock sync, distributed mutual exclusion), caching, replication (2PC, causal ordering, 4 client-centric consistency models, LWW conflict resolution), fault tolerance (2PC with WAL, bully election, auto-failover), and anti-entropy (gossip with Merkle trees).
