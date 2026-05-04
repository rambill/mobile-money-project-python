"""
Distributed Algorithms Implementation
- Bully Election
- Berkeley Clock Synchronization
- Distributed Locks (Coordinator-based)
- Two-Phase Commit
- Last-Writer-Wins Conflict Resolution
- Anti-Entropy with Merkle Trees
"""

import time
import json
import hashlib
import threading
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class VectorClock:
    """Vector clock for causal ordering"""
    
    def __init__(self, clock_dict: Optional[Dict[int, int]] = None):
        self.clock = clock_dict if clock_dict else {}
    
    def increment(self, server_id: int):
        """Increment the clock for a server"""
        self.clock[server_id] = self.clock.get(server_id, 0) + 1
    
    def update(self, other: 'VectorClock'):
        """Update with another vector clock (take max of each component)"""
        for server_id, count in other.clock.items():
            self.clock[server_id] = max(self.clock.get(server_id, 0), count)
    
    def compare(self, other: 'VectorClock') -> str:
        """
        Compare two vector clocks
        Returns: 'before', 'after', 'concurrent', or 'equal'
        """
        if self.clock == other.clock:
            return 'equal'
        
        all_keys = set(self.clock.keys()) | set(other.clock.keys())
        less = False
        greater = False
        
        for key in all_keys:
            self_val = self.clock.get(key, 0)
            other_val = other.clock.get(key, 0)
            
            if self_val < other_val:
                less = True
            elif self_val > other_val:
                greater = True
        
        if less and not greater:
            return 'before'
        elif greater and not less:
            return 'after'
        else:
            return 'concurrent'
    
    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps(self.clock)
    
    @staticmethod
    def from_json(json_str: str) -> 'VectorClock':
        """Deserialize from JSON"""
        try:
            clock_dict = json.loads(json_str)
            # Convert string keys to integers
            clock_dict = {int(k): v for k, v in clock_dict.items()}
            return VectorClock(clock_dict)
        except:
            return VectorClock()
    
    def __repr__(self):
        return f"VC{self.clock}"


class BullyElection:
    """Bully algorithm for leader election"""
    
    def __init__(self, server_id: int, all_server_ids: List[int], send_func):
        self.server_id = server_id
        self.all_server_ids = sorted(all_server_ids)
        self.send_func = send_func
        self.coordinator_id = None
        self.election_in_progress = False
        self.last_heartbeat = {}
        self.lock = threading.Lock()
    
    def start_election(self) -> Optional[int]:
        """Start a new election"""
        with self.lock:
            if self.election_in_progress:
                return None
            
            self.election_in_progress = True
        
        # Send ELECTION message to all higher-ID servers
        higher_servers = [sid for sid in self.all_server_ids if sid > self.server_id]
        
        if not higher_servers:
            # I'm the highest, declare victory
            self.declare_coordinator()
            return self.server_id
        
        # Send ELECTION messages
        responses = []
        for server_id in higher_servers:
            response = self.send_func(server_id, "ELECT_REQ", {})
            if response and response.get("type") == "ELECT_ANSWER":
                responses.append(server_id)
        
        # Wait for responses
        time.sleep(0.5)
        
        if not responses:
            # No one answered, I'm the coordinator
            self.declare_coordinator()
            return self.server_id
        else:
            # Someone answered, wait for their COORDINATOR message
            self.election_in_progress = False
            return None
    
    def declare_coordinator(self):
        """Declare self as coordinator"""
        self.coordinator_id = self.server_id
        self.election_in_progress = False
        
        # Broadcast COORDINATOR message
        for server_id in self.all_server_ids:
            if server_id != self.server_id:
                self.send_func(server_id, "ELECT_COORD", {"coordinator_id": self.server_id})
    
    def handle_election_request(self, from_server_id: int) -> Dict:
        """Handle incoming ELECTION message"""
        if from_server_id < self.server_id:
            # Start my own election
            threading.Thread(target=self.start_election, daemon=True).start()
            return {"type": "ELECT_ANSWER"}
        return {}
    
    def handle_coordinator_message(self, coordinator_id: int):
        """Handle COORDINATOR message"""
        with self.lock:
            self.coordinator_id = coordinator_id
            self.election_in_progress = False
            self.last_heartbeat[coordinator_id] = time.time()
    
    def handle_heartbeat(self, coordinator_id: int):
        """Handle heartbeat from coordinator"""
        with self.lock:
            self.last_heartbeat[coordinator_id] = time.time()
            if self.coordinator_id != coordinator_id:
                self.coordinator_id = coordinator_id
    
    def check_coordinator_alive(self, timeout: float) -> bool:
        """Check if coordinator is still alive"""
        if self.coordinator_id is None:
            return False
        
        with self.lock:
            last_hb = self.last_heartbeat.get(self.coordinator_id, 0)
            return (time.time() - last_hb) < timeout
    
    def is_coordinator(self) -> bool:
        """Check if this server is the coordinator"""
        return self.coordinator_id == self.server_id


class BerkeleyClockSync:
    """Berkeley algorithm for clock synchronization"""
    
    def __init__(self, server_id: int, send_func):
        self.server_id = server_id
        self.send_func = send_func
        self.time_offset = 0.0
    
    def sync_clocks(self, peer_ids: List[int]) -> Dict[int, float]:
        """
        Coordinator: Sync clocks with all peers
        Returns: Dictionary of adjustments sent to each peer
        """
        # Collect times from all peers
        times = {self.server_id: time.time()}
        
        for peer_id in peer_ids:
            response = self.send_func(peer_id, "CLOCK_REQ", {})
            if response and "time" in response:
                times[peer_id] = response["time"]
        
        if len(times) < 2:
            return {}
        
        # Calculate average time
        avg_time = sum(times.values()) / len(times)
        
        # Calculate adjustments
        adjustments = {}
        for server_id, server_time in times.items():
            adjustment = avg_time - server_time
            adjustments[server_id] = adjustment
            
            # Send adjustment to peers (not to self)
            if server_id != self.server_id:
                self.send_func(server_id, "CLOCK_ADJ", {"adjustment": adjustment})
        
        # Apply own adjustment
        self.time_offset += adjustments[self.server_id]
        
        return adjustments
    
    def get_time(self) -> float:
        """Get synchronized time"""
        return time.time() + self.time_offset
    
    def apply_adjustment(self, adjustment: float):
        """Apply clock adjustment from coordinator"""
        self.time_offset += adjustment


class DistributedLockManager:
    """Coordinator-based distributed lock manager"""
    
    def __init__(self, server_id: int):
        self.server_id = server_id
        self.locks = {}  # {resource: (holder_server_id, expiry_time)}
        self.lock = threading.Lock()
    
    def acquire_lock(self, resource: str, requester_id: int, timeout: float) -> bool:
        """Try to acquire a lock (coordinator only)"""
        with self.lock:
            current_time = time.time()
            
            # Check if lock exists and is not expired
            if resource in self.locks:
                holder, expiry = self.locks[resource]
                if current_time < expiry:
                    return False  # Lock is held
                else:
                    # Lock expired, can be acquired
                    del self.locks[resource]
            
            # Grant lock
            self.locks[resource] = (requester_id, current_time + timeout)
            return True
    
    def release_lock(self, resource: str, holder_id: int) -> bool:
        """Release a lock (coordinator only)"""
        with self.lock:
            if resource in self.locks:
                holder, _ = self.locks[resource]
                if holder == holder_id:
                    del self.locks[resource]
                    return True
            return False
    
    def cleanup_expired_locks(self):
        """Remove expired locks"""
        with self.lock:
            current_time = time.time()
            expired = [res for res, (_, exp) in self.locks.items() if current_time >= exp]
            for res in expired:
                del self.locks[res]


class TwoPhaseCommit:
    """Two-Phase Commit protocol implementation"""
    
    def __init__(self, server_id: int, send_func, wal_manager):
        self.server_id = server_id
        self.send_func = send_func
        self.wal_manager = wal_manager
        self.pending_txns = {}  # {txn_id: {votes, state}}
        self.lock = threading.Lock()
    
    def coordinate_commit(self, txn_id: str, operation: Dict, participants: List[int], timeout: float) -> bool:
        """
        Coordinate a 2PC transaction
        Returns: True if committed, False if aborted
        """
        # Phase 1: PREPARE
        self.wal_manager.log_prepare(txn_id, operation, participants)
        
        votes = {}
        for peer_id in participants:
            response = self.send_func(peer_id, "2PC_PREPARE", {
                "txn_id": txn_id,
                "operation": operation
            })
            
            if response and response.get("vote") == "YES":
                votes[peer_id] = "YES"
            else:
                votes[peer_id] = "NO"
        
        # Check if all voted YES
        all_yes = all(v == "YES" for v in votes.values())
        
        # Phase 2: COMMIT or ABORT
        if all_yes:
            self.wal_manager.log_commit(txn_id)
            for peer_id in participants:
                self.send_func(peer_id, "2PC_COMMIT", {"txn_id": txn_id})
            return True
        else:
            self.wal_manager.log_abort(txn_id)
            for peer_id in participants:
                self.send_func(peer_id, "2PC_ABORT", {"txn_id": txn_id})
            return False
    
    def handle_prepare(self, txn_id: str, operation: Dict) -> str:
        """
        Handle PREPARE message (participant)
        Returns: "YES" or "NO"
        """
        # Check if we can perform the operation
        # For now, always vote YES (can add validation logic)
        with self.lock:
            self.pending_txns[txn_id] = {"operation": operation, "state": "PREPARED"}
        return "YES"
    
    def handle_commit(self, txn_id: str) -> bool:
        """Handle COMMIT message (participant)"""
        with self.lock:
            if txn_id in self.pending_txns:
                self.pending_txns[txn_id]["state"] = "COMMITTED"
                return True
            return False
    
    def handle_abort(self, txn_id: str) -> bool:
        """Handle ABORT message (participant)"""
        with self.lock:
            if txn_id in self.pending_txns:
                self.pending_txns[txn_id]["state"] = "ABORTED"
                del self.pending_txns[txn_id]
                return True
            return False


class ConflictResolver:
    """Last-Writer-Wins conflict resolution"""
    
    @staticmethod
    def resolve(state1: Dict, state2: Dict) -> Dict:
        """
        Resolve conflict between two states using LWW
        state format: {
            'data': ...,
            'vector_clock': VectorClock,
            'physical_timestamp': float,
            'server_id': int
        }
        """
        vc1 = state1.get('vector_clock')
        vc2 = state2.get('vector_clock')
        
        comparison = vc1.compare(vc2)
        
        if comparison == 'after':
            return state1
        elif comparison == 'before':
            return state2
        elif comparison == 'concurrent':
            # Use physical timestamp as tiebreaker
            ts1 = state1.get('physical_timestamp', 0)
            ts2 = state2.get('physical_timestamp', 0)
            
            if ts1 > ts2:
                return state1
            elif ts2 > ts1:
                return state2
            else:
                # Use server ID as final tiebreaker
                sid1 = state1.get('server_id', 0)
                sid2 = state2.get('server_id', 0)
                return state1 if sid1 > sid2 else state2
        else:  # equal
            return state1


class MerkleTree:
    """Merkle tree for anti-entropy"""
    
    def __init__(self, depth: int = 4):
        self.depth = depth
        self.tree = {}
    
    def build(self, data: Dict[str, str]) -> str:
        """
        Build Merkle tree from data
        data: {key: value_hash}
        Returns: root hash
        """
        if not data:
            return hashlib.sha256(b"").hexdigest()
        
        # Sort keys for consistency
        sorted_keys = sorted(data.keys())
        
        # Build leaf hashes
        leaves = []
        for key in sorted_keys:
            leaf_hash = hashlib.sha256(f"{key}:{data[key]}".encode()).hexdigest()
            leaves.append(leaf_hash)
        
        # Build tree bottom-up
        current_level = leaves
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined = current_level[i] + current_level[i + 1]
                else:
                    combined = current_level[i]
                parent_hash = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(parent_hash)
            current_level = next_level
        
        return current_level[0] if current_level else hashlib.sha256(b"").hexdigest()
    
    @staticmethod
    def hash_value(value: str) -> str:
        """Hash a single value"""
        return hashlib.sha256(value.encode()).hexdigest()


class AntiEntropy:
    """Anti-entropy using gossip and Merkle trees"""
    
    def __init__(self, server_id: int, send_func, get_data_func):
        self.server_id = server_id
        self.send_func = send_func
        self.get_data_func = get_data_func
        self.merkle = MerkleTree()
    
    def request_full_state(self, peer_id: int) -> Dict:
        """
        Request full state from a peer (for new/empty servers)
        Supports chunked transfer for large datasets
        Returns: Dictionary with all accounts from peer
        """
        response = self.send_func(peer_id, "STATE_REQUEST", {
            "requester": self.server_id
        })
        
        if not response:
            return {"success": False, "error": "No response"}
        
        # Check if response is chunked
        if response.get("chunked"):
            # Receive all chunks
            total_chunks = response.get("total_chunks", 0)
            chunks = {0: response.get("data", "")}  # First chunk
            
            # Request remaining chunks
            for chunk_id in range(1, total_chunks):
                chunk_response = self.send_func(peer_id, "STATE_REQUEST_CHUNK", {
                    "requester": self.server_id,
                    "chunk_id": chunk_id
                })
                
                if chunk_response and chunk_response.get("success"):
                    chunks[chunk_id] = chunk_response.get("data", "")
                else:
                    return {"success": False, "error": f"Failed to receive chunk {chunk_id}"}
            
            # Reassemble chunks
            full_data = "".join(chunks[i] for i in range(total_chunks))
            try:
                accounts = json.loads(full_data)
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"Failed to parse chunked data: {e}"}
        else:
            # Single response (not chunked)
            accounts = response.get("accounts", {})
        
        return {
            "success": True,
            "accounts": accounts,
            "count": len(accounts)
        }
    
    def gossip_with_peer(self, peer_id: int) -> Dict:
        """
        Perform gossip exchange with a peer
        Returns: Dictionary with sync statistics
        """
        # Get local data hashes
        local_data = self.get_data_func()
        local_hashes = {k: MerkleTree.hash_value(str(v)) for k, v in local_data.items()}
        local_root = self.merkle.build(local_hashes)
        
        # Send Merkle root to peer
        response = self.send_func(peer_id, "GOSSIP_MERKLE", {
            "root_hash": local_root,
            "data_hashes": local_hashes
        })
        
        if not response:
            return {"synced": 0, "error": "No response"}
        
        peer_hashes = response.get("data_hashes", {})
        
        # Find differences
        all_keys = set(local_hashes.keys()) | set(peer_hashes.keys())
        differences = []
        
        for key in all_keys:
            local_hash = local_hashes.get(key)
            peer_hash = peer_hashes.get(key)
            
            if local_hash != peer_hash:
                differences.append(key)
        
        return {
            "synced": len(differences),
            "differences": differences,
            "peer_id": peer_id
        }
