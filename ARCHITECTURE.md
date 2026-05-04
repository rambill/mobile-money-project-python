# Architecture Documentation

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DISTRIBUTED MOBILE MONEY SYSTEM                  │
│                                                                       │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      │
│  │   Server 1   │◄────►│   Server 2   │◄────►│   Server 3   │      │
│  │  (Kampala)   │      │  (Mbarara)   │      │   (Gulu)     │      │
│  │              │      │              │      │              │      │
│  │ Port: 6001   │      │ Port: 6002   │      │ Port: 6003   │      │
│  │ Rep:  6101   │      │ Rep:  6102   │      │ Rep:  6103   │      │
│  └──────▲───────┘      └──────▲───────┘      └──────▲───────┘      │
│         │                     │                     │               │
│         │    Peer-to-Peer Replication (2PC)        │               │
│         │                     │                     │               │
│         └─────────────────────┴─────────────────────┘               │
│                               │                                     │
│                               │ UDP Discovery (Port 5999)           │
│                               │                                     │
│                     ┌─────────▼─────────┐                          │
│                     │      Client       │                          │
│                     │  (Auto-discover)  │                          │
│                     └───────────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
```

## Server Internal Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          SERVER NODE                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────┐  ┌────────────────────┐  ┌───────────────┐ │
│  │   RPC Server       │  │  Replication Mgr   │  │   Discovery   │ │
│  │   (UDP :600X)      │  │  (UDP :610X)       │  │  (UDP :5999)  │ │
│  ├────────────────────┤  ├────────────────────┤  ├───────────────┤ │
│  │ • Client requests  │  │ • Election msgs    │  │ • Broadcasts  │ │
│  │ • REGISTER         │  │ • Clock sync       │  │ • Responds to │ │
│  │ • BALANCE          │  │ • 2PC coordination │  │   DISCOVER    │ │
│  │ • DEPOSIT          │  │ • Gossip/Merkle    │  │ • Load info   │ │
│  │ • WITHDRAW         │  │ • Lock requests    │  │               │ │
│  └────────────────────┘  └────────────────────┘  └───────────────┘ │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│                     DISTRIBUTED ALGORITHMS                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Election   │  │  Clock Sync  │  │  Lock Mgr    │              │
│  │   (Bully)    │  │  (Berkeley)  │  │ (Coordinator)│              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   2PC        │  │ Anti-Entropy │  │   Conflict   │              │
│  │ (PREPARE/    │  │  (Gossip +   │  │  Resolution  │              │
│  │  COMMIT)     │  │   Merkle)    │  │    (LWW)     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│                         DATA LAYER                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │                    DataStore (SQLite)                       │     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │ • Accounts (with vector clocks)                            │     │
│  │ • Transactions log                                         │     │
│  │ • Replication log (exactly-once)                           │     │
│  │ • Server registry                                          │     │
│  │ • Cache (TTL-based)                                        │     │
│  │ • WAL for 2PC                                              │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Write Operation Flow

```
┌─────────┐                                                    ┌─────────┐
│ Client  │                                                    │ Server  │
└────┬────┘                                                    └────┬────┘
     │                                                              │
     │  1. REQ|id|DEPOSIT|phone|pin|amount|write_vc|read_vc       │
     │─────────────────────────────────────────────────────────────>│
     │                                                              │
     │                                    2. Verify PIN             │
     │                                    3. Check Monotonic Writes │
     │                                    4. Check Writes-Follow-   │
     │                                       Reads                  │
     │                                                              │
     │                                    5. Acquire Lock           │
     │                                       (from Coordinator)     │
     │                                                              │
     │                                    6. Apply locally          │
     │                                       (SQLite + VC++)        │
     │                                                              │
     │                                    ┌──────────────────┐     │
     │                                    │   2PC Protocol   │     │
     │                                    ├──────────────────┤     │
     │                                    │ PREPARE → Peers  │     │
     │                                    │ ← VOTE_YES       │     │
     │                                    │ COMMIT → Peers   │     │
     │                                    │ (Apply write)    │     │
     │                                    └──────────────────┘     │
     │                                                              │
     │                                    7. Release Lock           │
     │                                                              │
     │  8. RES|id|OK|message|balance|vector_clock                  │
     │<─────────────────────────────────────────────────────────────│
     │                                                              │
```

## Read Operation Flow

```
┌─────────┐                                                    ┌─────────┐
│ Client  │                                                    │ Server  │
└────┬────┘                                                    └────┬────┘
     │                                                              │
     │  1. REQ|id|BALANCE|phone|pin                                │
     │─────────────────────────────────────────────────────────────>│
     │                                                              │
     │                                    2. Verify PIN             │
     │                                                              │
     │                                    3. Check cache            │
     │                                       (10s TTL)              │
     │                                                              │
     │                                    4. Query SQLite           │
     │                                                              │
     │                                    5. Update read VC         │
     │                                                              │
     │  6. RES|id|OK|message|balance|vector_clock                  │
     │<─────────────────────────────────────────────────────────────│
     │                                                              │
     │  7. Client updates last_read_vc                             │
     │                                                              │
```

## Election Flow (Bully Algorithm)

```
Server 1 (ID=1)    Server 2 (ID=2)    Server 3 (ID=3)
     │                  │                  │
     │                  │                  │ Coordinator timeout
     │                  │                  │ detected
     │                  │                  │
     │   ELECTION       │   ELECTION       │
     │<─────────────────┼──────────────────┤
     │                  │                  │
     │   ANSWER         │   ANSWER         │
     ├─────────────────>│<─────────────────┤
     │                  │                  │
     │                  │ I'm highest ID   │
     │                  │ alive, I win!    │
     │                  │                  │
     │  COORDINATOR     │  COORDINATOR     │
     │<─────────────────┼─────────────────>│
     │  (ID=2)          │  (ID=2)          │
     │                  │                  │
     │                  │ Start sending    │
     │                  │ heartbeats       │
     │                  │                  │
     │   HEARTBEAT      │   HEARTBEAT      │
     │<─────────────────┼─────────────────>│
     │                  │                  │
```

## 2-Phase Commit Flow

```
Coordinator                Participant 1           Participant 2
     │                          │                       │
     │  PREPARE (txn, op)       │                       │
     ├─────────────────────────>│                       │
     │                          │                       │
     │  PREPARE (txn, op)       │                       │
     ├──────────────────────────┼──────────────────────>│
     │                          │                       │
     │                          │ Check if can commit   │
     │                          │ Log to WAL            │
     │                          │                       │
     │       VOTE_YES           │                       │
     │<─────────────────────────┤                       │
     │                          │                       │
     │                          │       VOTE_YES        │
     │<─────────────────────────┼───────────────────────┤
     │                          │                       │
     │ All voted YES            │                       │
     │ Decision: COMMIT         │                       │
     │                          │                       │
     │  COMMIT                  │                       │
     ├─────────────────────────>│                       │
     │                          │                       │
     │  COMMIT                  │                       │
     ├──────────────────────────┼──────────────────────>│
     │                          │                       │
     │                          │ Apply operation       │
     │                          │ Update VC             │
     │                          │                       │
```

## Vector Clock Evolution

```
Initial State:
Server 1: VC = {1:0, 2:0, 3:0}
Server 2: VC = {1:0, 2:0, 3:0}
Server 3: VC = {1:0, 2:0, 3:0}

After Server 1 writes:
Server 1: VC = {1:1, 2:0, 3:0}  ← Incremented
Server 2: VC = {1:0, 2:0, 3:0}  (not yet replicated)
Server 3: VC = {1:0, 2:0, 3:0}  (not yet replicated)

After replication:
Server 1: VC = {1:1, 2:0, 3:0}
Server 2: VC = {1:1, 2:0, 3:0}  ← Updated
Server 3: VC = {1:1, 2:0, 3:0}  ← Updated

After Server 2 writes:
Server 1: VC = {1:1, 2:1, 3:0}  ← Updated after replication
Server 2: VC = {1:1, 2:1, 3:0}  ← Incremented
Server 3: VC = {1:1, 2:1, 3:0}  ← Updated after replication

Concurrent writes (before replication):
Server 1: VC = {1:2, 2:1, 3:0}  ← Server 1 writes
Server 2: VC = {1:1, 2:2, 3:0}  ← Server 2 writes (concurrent!)
Server 3: VC = {1:1, 2:1, 3:0}

Conflict detected: VC1 and VC2 are concurrent
Resolution: Use LWW (physical timestamp + server ID)
```

## Client-Centric Consistency

```
┌─────────────────────────────────────────────────────────────┐
│                  CLIENT STATE                                │
├─────────────────────────────────────────────────────────────┤
│ last_write_server: 1                                        │
│ last_write_time: 1234567890.5                               │
│ last_write_vc: {1:5, 2:3, 3:2}                              │
│ last_read_vc: {1:5, 2:3, 3:2}                               │
└─────────────────────────────────────────────────────────────┘
         │
         │ Write operation
         ▼
┌─────────────────────────────────────────────────────────────┐
│              MONOTONIC WRITES CHECK                          │
│  Client sends: last_write_vc = {1:5, 2:3, 3:2}              │
│  Server has:   local_vc = {1:6, 2:3, 3:2}                   │
│  Check: local_vc >= last_write_vc? YES → Allow              │
└─────────────────────────────────────────────────────────────┘
         │
         │ Read operation
         ▼
┌─────────────────────────────────────────────────────────────┐
│              READ-YOUR-WRITES CHECK                          │
│  Time since last write: 2.3s < 5s TTL                       │
│  Route to: last_write_server (Server 1)                     │
│  Ensures: Client sees its own writes                        │
└─────────────────────────────────────────────────────────────┘
```

## Anti-Entropy (Gossip) Flow

```
Server 1                                    Server 2
   │                                           │
   │ Every 60 seconds                          │
   │                                           │
   │ 1. Build Merkle tree of all accounts     │
   │    Root hash: abc123...                  │
   │                                           │
   │  GOSSIP_MERKLE                            │
   │  {root_hash, data_hashes}                │
   ├──────────────────────────────────────────>│
   │                                           │
   │                                           │ 2. Build own Merkle tree
   │                                           │    Root hash: abc456...
   │                                           │
   │                                           │ 3. Compare hashes
   │                                           │    Find differences
   │                                           │
   │  GOSSIP_RESPONSE                          │
   │  {data_hashes}                            │
   │<──────────────────────────────────────────┤
   │                                           │
   │ 4. Compare data_hashes                    │
   │    Identify differing accounts            │
   │                                           │
   │ 5. Request full data for differences      │
   │                                           │
   │ 6. Apply conflict resolution (LWW)        │
   │                                           │
```

## Data Flow Summary

```
┌──────────────────────────────────────────────────────────────┐
│                      DATA FLOW                                │
└──────────────────────────────────────────────────────────────┘

Client Request
     │
     ▼
┌─────────────┐
│ RPC Server  │ ← UDP :600X
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Validate   │ ← PIN, Monotonic checks
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Acquire     │ ← Distributed lock
│ Lock        │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Apply       │ ← SQLite + Vector clock
│ Locally     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 2PC         │ ← Replicate to all peers
│ Replication │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Release     │ ← Free lock
│ Lock        │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Response    │ ← Send result to client
└─────────────┘
```

## Network Topology

```
Geographic Distribution (Uganda Example):

        ┌─────────────────────────────────────┐
        │         UGANDA                       │
        │                                      │
        │    ┌──────┐                          │
        │    │Server│ Gulu (Northern)          │
        │    │  3   │                          │
        │    └──────┘                          │
        │       │                              │
        │       │                              │
        │    ┌──────┐                          │
        │    │Server│ Kampala (Central)        │
        │    │  1   │ ← Coordinator            │
        │    └──────┘                          │
        │       │                              │
        │       │                              │
        │    ┌──────┐                          │
        │    │Server│ Mbarara (Western)        │
        │    │  2   │                          │
        │    └──────┘                          │
        │                                      │
        └─────────────────────────────────────┘

All servers connected via:
- Internet/VPN
- UDP ports 600X (RPC) and 610X (Replication)
- Latency: 10-100ms between regions
```

## Component Interaction Matrix

```
┌──────────────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│              │ RPC │ Rep │Elect│Clock│Lock │ 2PC │Goss │
├──────────────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│ RPC Server   │  -  │  →  │  →  │  →  │  →  │  →  │  -  │
│ Replication  │  ←  │  -  │  ←  │  ←  │  ←  │  ←  │  ←  │
│ Election     │  -  │  →  │  -  │  -  │  -  │  -  │  -  │
│ Clock Sync   │  -  │  →  │  -  │  -  │  -  │  -  │  -  │
│ Lock Manager │  ←  │  →  │  -  │  -  │  -  │  -  │  -  │
│ 2PC          │  ←  │  →  │  -  │  -  │  -  │  -  │  -  │
│ Gossip       │  -  │  →  │  -  │  -  │  -  │  -  │  -  │
└──────────────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘

Legend: → sends to, ← receives from, - no interaction
```

---

This architecture implements a complete distributed system with:
- **No single point of failure**
- **Automatic failover and recovery**
- **Strong consistency guarantees**
- **Efficient replication**
- **Scalable design**
