# Project Index - Distributed Mobile Money System

## 📚 Documentation Files

### Getting Started
- **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
  - Installation steps
  - First-time setup
  - Basic operations
  - Common issues

- **[README.md](README.md)** - Complete system documentation
  - Feature overview
  - Architecture description
  - Configuration guide
  - Troubleshooting

### Deployment & Operations
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
  - Network setup
  - Multi-machine deployment
  - Firewall configuration
  - Performance tuning
  - Security considerations

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
  - Component diagrams
  - Data flow diagrams
  - Protocol specifications
  - Interaction patterns

### Project Information
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Project overview
  - What's been built
  - Features implemented
  - Code statistics
  - Learning outcomes

- **[FIXES_APPLIED.md](FIXES_APPLIED.md)** - Recent bug fixes
  - Account persistence fix
  - Replication fixes
  - Timeout fixes
  - Testing guide

- **[INDEX.md](INDEX.md)** - This file
  - File navigation
  - Quick reference

## 💻 Source Code Files

### Core System
- **[server.py](server.py)** (~450 lines)
  - Main server process
  - RPC handler
  - Replication manager
  - Background tasks
  - Entry point: `python server.py <id>`

- **[client.py](client.py)** (~350 lines)
  - Interactive client
  - Server discovery
  - Consistency tracking
  - User interface
  - Entry point: `python client.py`

- **[admin.py](admin.py)** (~250 lines)
  - Admin console
  - Server monitoring
  - Consistency checks
  - Integration tests
  - Entry point: `python admin.py <command>`

### Libraries & Modules
- **[distributed.py](distributed.py)** (~500 lines)
  - VectorClock - Causal ordering
  - BullyElection - Leader election
  - BerkeleyClockSync - Clock synchronization
  - DistributedLockManager - Mutual exclusion
  - TwoPhaseCommit - Atomic replication
  - ConflictResolver - LWW resolution
  - MerkleTree - Anti-entropy
  - AntiEntropy - Gossip protocol

- **[config.py](config.py)** (~100 lines)
  - Server configuration
  - Network settings
  - Feature flags
  - Timeouts and intervals
  - Helper functions

### Database
- **[mobile.sql](mobile.sql)** (~60 lines)
  - Database schema
  - Tables: accounts, transactions, replication_log, etc.
  - Indexes for performance
  - Constraints

## 🧪 Testing & Utilities

- **[test_system.py](test_system.py)** (~300 lines)
  - Unit tests for all components
  - Vector clock tests
  - Conflict resolution tests
  - Merkle tree tests
  - Database schema tests
  - Entry point: `python test_system.py`

- **[test_persistence.py](test_persistence.py)** (~50 lines)
  - Check database persistence
  - Verify account data across servers
  - Entry point: `python test_persistence.py`

## ⚙️ Configuration Files

- **[servers.json](servers.json)**
  - Server definitions
  - IP addresses and ports
  - Region information
  - Active/inactive status

- **[requirements.txt](requirements.txt)**
  - Python dependencies (none!)
  - Optional dev tools

- **[.gitignore](.gitignore)**
  - Git ignore patterns
  - Database files
  - Logs and temporary files

## 🚀 Startup Scripts

### Linux/macOS
- **[start_servers.sh](start_servers.sh)**
  - Start all servers
  - Usage: `./start_servers.sh`

- **[stop_servers.sh](stop_servers.sh)**
  - Stop all servers
  - Usage: `./stop_servers.sh`

### Windows
- **[start_servers.bat](start_servers.bat)**
  - Start all servers in separate windows
  - Usage: `start_servers.bat`

## 📖 Quick Reference

### Common Commands

```bash
# Start servers
./start_servers.sh              # Linux/macOS
start_servers.bat               # Windows
python server.py 1              # Manual start

# Run client
python client.py

# Admin commands
python admin.py status          # Server status
python admin.py sync            # Consistency check
python admin.py test            # Integration tests

# Run tests
python test_system.py

# Stop servers
./stop_servers.sh               # Linux/macOS
# Close windows or Ctrl+C       # Windows
```

### File Sizes

| File | Lines | Purpose |
|------|-------|---------|
| server.py | ~450 | Main server |
| distributed.py | ~500 | Algorithms |
| client.py | ~350 | Client UI |
| admin.py | ~250 | Admin tools |
| test_system.py | ~300 | Tests |
| config.py | ~100 | Configuration |
| mobile.sql | ~60 | Schema |
| **Total** | **~2000** | **Complete system** |

### Documentation Sizes

| File | Purpose |
|------|---------|
| README.md | Main documentation (~500 lines) |
| DEPLOYMENT.md | Deployment guide (~400 lines) |
| QUICKSTART.md | Quick start (~250 lines) |
| ARCHITECTURE.md | Architecture diagrams (~400 lines) |
| PROJECT_SUMMARY.md | Project overview (~350 lines) |
| INDEX.md | This file (~200 lines) |

## 🎯 Learning Path

### Beginner
1. Read [QUICKSTART.md](QUICKSTART.md)
2. Start servers and run client
3. Try basic operations (register, deposit, balance)
4. Read [README.md](README.md) overview section

### Intermediate
1. Read [ARCHITECTURE.md](ARCHITECTURE.md)
2. Explore [distributed.py](distributed.py) code
3. Run [test_system.py](test_system.py)
4. Try [admin.py](admin.py) commands
5. Read [server.py](server.py) implementation

### Advanced
1. Read [DEPLOYMENT.md](DEPLOYMENT.md)
2. Deploy across multiple machines
3. Modify [config.py](config.py) settings
4. Add new features to [server.py](server.py)
5. Implement additional algorithms in [distributed.py](distributed.py)

## 🔍 Code Navigation

### Finding Specific Features

**Vector Clocks:**
- Implementation: `distributed.py` → `VectorClock` class
- Usage: `server.py` → `DataStore.update_balance()`
- Tests: `test_system.py` → `test_vector_clocks()`

**2-Phase Commit:**
- Implementation: `distributed.py` → `TwoPhaseCommit` class
- Usage: `server.py` → `_process_rpc()` → deposit/withdraw
- Configuration: `config.py` → `TWO_PC_ENABLED`

**Bully Election:**
- Implementation: `distributed.py` → `BullyElection` class
- Usage: `server.py` → `start()` → election
- Background: `server.py` → `_coordinator_tasks()`

**Client Consistency:**
- Implementation: `client.py` → consistency methods
- Read-your-writes: `_prefer_last_write_server()`
- Monotonic writes: `_check_monotonic_writes()`

**Anti-Entropy:**
- Implementation: `distributed.py` → `AntiEntropy` class
- Usage: `server.py` → `_anti_entropy_task()`
- Merkle trees: `distributed.py` → `MerkleTree` class

## 📊 System Statistics

### Code Metrics
- **Total Lines**: ~2,000
- **Total Files**: 18
- **Languages**: Python, SQL, Bash, Markdown
- **External Dependencies**: 0
- **Distributed Concepts**: 15

### Feature Coverage
- ✅ Peer-to-peer replication
- ✅ Vector clocks
- ✅ 2-Phase Commit
- ✅ Bully election
- ✅ Berkeley clock sync
- ✅ Distributed locks
- ✅ Client-centric consistency (4 models)
- ✅ Conflict resolution (LWW)
- ✅ Anti-entropy (Gossip + Merkle)
- ✅ Automatic failover
- ✅ WAL recovery
- ✅ Exactly-once delivery

## 🛠️ Development Workflow

### Adding a New Feature
1. Update schema in `mobile.sql` if needed
2. Add algorithm to `distributed.py` if needed
3. Implement in `server.py`
4. Add client support in `client.py`
5. Add admin command in `admin.py` if needed
6. Write tests in `test_system.py`
7. Update documentation

### Testing Changes
1. Run unit tests: `python test_system.py`
2. Start servers: `./start_servers.sh`
3. Run integration tests: `python admin.py test`
4. Check consistency: `python admin.py sync`
5. Manual testing: `python client.py`

### Debugging
1. Check server logs (stdout)
2. Inspect database: `sqlite3 data/server_1.db`
3. Check WAL: `cat wal/server_1.wal`
4. Monitor status: `python admin.py status`
5. Add debug prints to code

## 📞 Support & Resources

### Documentation
- Start here: [QUICKSTART.md](QUICKSTART.md)
- Full docs: [README.md](README.md)
- Deployment: [DEPLOYMENT.md](DEPLOYMENT.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)

### Troubleshooting
- Common issues: [QUICKSTART.md](QUICKSTART.md) → Common Issues
- Network problems: [DEPLOYMENT.md](DEPLOYMENT.md) → Troubleshooting
- Configuration: [README.md](README.md) → Configuration

### Learning Resources
- Distributed systems concepts: [README.md](README.md) → Features table
- Code examples: All `.py` files have inline comments
- Test examples: [test_system.py](test_system.py)

## 🎓 Educational Value

This project teaches:
1. **Distributed Architecture** - Peer-to-peer design
2. **Consistency Models** - Causal, eventual, client-centric
3. **Replication** - Active replication, 2PC
4. **Consensus** - Bully election algorithm
5. **Clock Synchronization** - Vector clocks, Berkeley
6. **Conflict Resolution** - Last-Writer-Wins
7. **Fault Tolerance** - Failover, recovery, WAL
8. **Anti-Entropy** - Gossip, Merkle trees
9. **Distributed Locking** - Coordinator-based
10. **Network Programming** - UDP, RPC, discovery

## 🚦 Status Indicators

### System Health
```bash
python admin.py status    # Check all servers
python admin.py sync      # Check consistency
python admin.py test      # Run tests
```

### Expected Output
- ✅ All servers responding
- ✅ Accounts consistent across servers
- ✅ All tests passing
- ✅ No orphaned transactions

## 📝 Notes

- **No external dependencies** - Uses only Python standard library
- **Production-ready** - Includes error handling, logging, recovery
- **Well-documented** - Comprehensive inline and external docs
- **Tested** - Unit tests and integration tests included
- **Scalable** - Add servers by editing config
- **Educational** - Clear code with learning in mind

---

**Quick Links:**
- [Get Started](QUICKSTART.md) | [Full Docs](README.md) | [Deploy](DEPLOYMENT.md) | [Architecture](ARCHITECTURE.md)

**Total Project Size:** ~2,000 lines of code + ~2,000 lines of documentation = **4,000 lines total**
