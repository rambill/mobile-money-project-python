#!/usr/bin/env python3
"""
Distributed Mobile Money Server
Implements peer-to-peer replicated architecture with full distributed systems features
"""

import socket
import threading
import time
import json
import sqlite3
import os
import sys
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import config
from distributed import (
    VectorClock, BullyElection, BerkeleyClockSync,
    DistributedLockManager, TwoPhaseCommit, ConflictResolver,
    MerkleTree, AntiEntropy
)


class WALManager:
    """Write-Ahead Log Manager for 2PC"""
    
    def __init__(self, server_id: int):
        self.server_id = server_id
        self.wal_dir = config.TWO_PC_WAL_DIR
        os.makedirs(self.wal_dir, exist_ok=True)
        self.wal_file = os.path.join(self.wal_dir, f"server_{server_id}.wal")
    
    def log_prepare(self, txn_id: str, operation: Dict, participants: List[int]):
        """Log PREPARE phase"""
        with open(self.wal_file, 'a') as f:
            entry = {
                "txn_id": txn_id,
                "state": "PREPARE",
                "operation": operation,
                "participants": participants,
                "timestamp": time.time()
            }
            f.write(json.dumps(entry) + "\n")
    
    def log_commit(self, txn_id: str):
        """Log COMMIT phase"""
        with open(self.wal_file, 'a') as f:
            entry = {
                "txn_id": txn_id,
                "state": "COMMIT",
                "timestamp": time.time()
            }
            f.write(json.dumps(entry) + "\n")
    
    def log_abort(self, txn_id: str):
        """Log ABORT phase"""
        with open(self.wal_file, 'a') as f:
            entry = {
                "txn_id": txn_id,
                "state": "ABORT",
                "timestamp": time.time()
            }
            f.write(json.dumps(entry) + "\n")
    
    def recover(self) -> List[Dict]:
        """Recover from WAL on startup"""
        if not os.path.exists(self.wal_file):
            return []
        
        transactions = {}
        with open(self.wal_file, 'r') as f:
            for line in f:
                entry = json.loads(line.strip())
                txn_id = entry["txn_id"]
                
                if entry["state"] == "PREPARE":
                    transactions[txn_id] = entry
                elif entry["state"] in ["COMMIT", "ABORT"]:
                    if txn_id in transactions:
                        transactions[txn_id]["final_state"] = entry["state"]
        
        # Return orphaned transactions (PREPARE without COMMIT/ABORT)
        orphaned = [txn for txn in transactions.values() if "final_state" not in txn]
        return orphaned


class DataStore:
    """SQLite-based data store with vector clocks"""
    
    def __init__(self, server_id: int):
        self.server_id = server_id
        self.db_dir = config.DB_DIR
        
        # Ensure data directory exists
        os.makedirs(self.db_dir, exist_ok=True)
        
        self.db_path = os.path.join(self.db_dir, config.DB_NAME_TEMPLATE.format(server_id))
        
        # Check if database file exists
        db_exists = os.path.exists(self.db_path)
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        
        if db_exists:
            print(f"[Server {server_id}] Found existing database at {self.db_path}")
        else:
            print(f"[Server {server_id}] Creating new database at {self.db_path}")
        
        self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema"""
        # Check if database already exists (has tables)
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'"
        )
        
        if cursor.fetchone() is None:
            # Database is new, create schema
            print(f"[Server {self.server_id}] Creating new database schema...")
            with open('mobile.sql', 'r') as f:
                schema = f.read()
            
            with self.lock:
                self.conn.executescript(schema)
                self.conn.commit()
        else:
            print(f"[Server {self.server_id}] Using existing database")
    
    def create_account(self, phone: str, pin: str) -> Tuple[bool, str, VectorClock]:
        """Create a new account"""
        with self.lock:
            try:
                # Check if account exists
                cursor = self.conn.execute("SELECT phone FROM accounts WHERE phone = ?", (phone,))
                if cursor.fetchone():
                    return False, "Account already exists", VectorClock()
                
                # Create account with initial vector clock
                vc = VectorClock()
                vc.increment(self.server_id)
                
                self.conn.execute(
                    "INSERT INTO accounts (phone, pin, balance, vector_clock, physical_timestamp, last_modified_by) VALUES (?, ?, ?, ?, ?, ?)",
                    (phone, pin, 0.0, vc.to_json(), time.time(), self.server_id)
                )
                self.conn.commit()
                
                return True, "Account created successfully", vc
            except Exception as e:
                return False, f"Error: {str(e)}", VectorClock()
    
    def get_account(self, phone: str) -> Optional[Dict]:
        """Get account details"""
        with self.lock:
            cursor = self.conn.execute(
                "SELECT * FROM accounts WHERE phone = ?", (phone,)
            )
            row = cursor.fetchone()
            
            if row:
                return {
                    "phone": row["phone"],
                    "balance": row["balance"],
                    "vector_clock": VectorClock.from_json(row["vector_clock"]),
                    "physical_timestamp": row["physical_timestamp"],
                    "last_modified_by": row["last_modified_by"]
                }
            return None
    
    def verify_pin(self, phone: str, pin: str) -> bool:
        """Verify account PIN"""
        with self.lock:
            cursor = self.conn.execute(
                "SELECT pin FROM accounts WHERE phone = ?", (phone,)
            )
            row = cursor.fetchone()
            if row:
                stored_pin = row["pin"]
                result = stored_pin == pin
                if not result:
                    print(f"[DataStore] PIN mismatch for {phone}: stored={'*' * len(stored_pin)}, provided={'*' * len(pin)}")
                return result
            else:
                print(f"[DataStore] Account not found: {phone}")
                return False
    
    def update_balance(self, phone: str, amount: float, operation: str, vc: VectorClock) -> Tuple[bool, str, float]:
        """Update account balance"""
        with self.lock:
            try:
                # Get account directly without calling get_account (avoid nested lock)
                cursor = self.conn.execute(
                    "SELECT * FROM accounts WHERE phone = ?", (phone,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return False, "Account not found", 0.0
                
                current_balance = row["balance"]
                new_balance = current_balance + amount
                
                if new_balance < 0:
                    return False, "Insufficient balance", current_balance
                
                # Update vector clock
                vc.increment(self.server_id)
                
                # Update account
                self.conn.execute(
                    "UPDATE accounts SET balance = ?, vector_clock = ?, physical_timestamp = ?, last_modified_by = ? WHERE phone = ?",
                    (new_balance, vc.to_json(), time.time(), self.server_id, phone)
                )
                
                # Log transaction
                self.conn.execute(
                    "INSERT INTO transactions (phone, type, amount, balance_after, vector_clock, server_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (phone, operation, amount, new_balance, vc.to_json(), self.server_id)
                )
                
                self.conn.commit()
                
                return True, "Success", new_balance
            except Exception as e:
                self.conn.rollback()
                return False, f"Error: {str(e)}", 0.0
    
    def get_all_accounts(self) -> Dict[str, Dict]:
        """Get all accounts for anti-entropy"""
        with self.lock:
            cursor = self.conn.execute("SELECT * FROM accounts")
            accounts = {}
            for row in cursor.fetchall():
                accounts[row["phone"]] = {
                    "balance": row["balance"],
                    "vector_clock": row["vector_clock"],
                    "physical_timestamp": row["physical_timestamp"],
                    "last_modified_by": row["last_modified_by"]
                }
            return accounts
    
    def atomic_deposit(self, phone: str, amount: float) -> Tuple[bool, str, float, VectorClock]:
        """Atomically deposit money (thread-safe for concurrent clients)"""
        with self.lock:
            try:
                # Get account and update in one atomic operation
                cursor = self.conn.execute(
                    "SELECT * FROM accounts WHERE phone = ?", (phone,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return False, "Account not found", 0.0, VectorClock()
                
                current_balance = row["balance"]
                new_balance = current_balance + amount
                
                # Get and increment vector clock
                vc = VectorClock.from_json(row["vector_clock"])
                vc.increment(self.server_id)
                
                # Update account
                self.conn.execute(
                    "UPDATE accounts SET balance = ?, vector_clock = ?, physical_timestamp = ?, last_modified_by = ? WHERE phone = ?",
                    (new_balance, vc.to_json(), time.time(), self.server_id, phone)
                )
                
                # Log transaction
                self.conn.execute(
                    "INSERT INTO transactions (phone, type, amount, balance_after, vector_clock, server_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (phone, "DEPOSIT", amount, new_balance, vc.to_json(), self.server_id)
                )
                
                self.conn.commit()
                
                return True, "Success", new_balance, vc
            except Exception as e:
                self.conn.rollback()
                return False, f"Error: {str(e)}", 0.0, VectorClock()
    
    def atomic_withdraw(self, phone: str, amount: float) -> Tuple[bool, str, float, VectorClock]:
        """Atomically withdraw money (thread-safe for concurrent clients)"""
        with self.lock:
            try:
                # Get account and update in one atomic operation
                cursor = self.conn.execute(
                    "SELECT * FROM accounts WHERE phone = ?", (phone,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return False, "Account not found", 0.0, VectorClock()
                
                current_balance = row["balance"]
                new_balance = current_balance - amount
                
                if new_balance < 0:
                    return False, "Insufficient balance", current_balance, VectorClock.from_json(row["vector_clock"])
                
                # Get and increment vector clock
                vc = VectorClock.from_json(row["vector_clock"])
                vc.increment(self.server_id)
                
                # Update account
                self.conn.execute(
                    "UPDATE accounts SET balance = ?, vector_clock = ?, physical_timestamp = ?, last_modified_by = ? WHERE phone = ?",
                    (new_balance, vc.to_json(), time.time(), self.server_id, phone)
                )
                
                # Log transaction
                self.conn.execute(
                    "INSERT INTO transactions (phone, type, amount, balance_after, vector_clock, server_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (phone, "WITHDRAW", -amount, new_balance, vc.to_json(), self.server_id)
                )
                
                self.conn.commit()
                
                return True, "Success", new_balance, vc
            except Exception as e:
                self.conn.rollback()
                return False, f"Error: {str(e)}", 0.0, VectorClock()
    
    def atomic_transfer(self, from_phone: str, to_phone: str, amount: float) -> Tuple[bool, str, float, VectorClock, VectorClock]:
        """Atomically transfer money between accounts (thread-safe for concurrent clients)"""
        with self.lock:
            try:
                # Get both accounts in one atomic operation
                cursor = self.conn.execute(
                    "SELECT * FROM accounts WHERE phone IN (?, ?)", (from_phone, to_phone)
                )
                rows = cursor.fetchall()
                
                if len(rows) != 2:
                    if len(rows) == 0:
                        return False, "Sender and recipient accounts not found", 0.0, VectorClock(), VectorClock()
                    elif rows[0]["phone"] == from_phone:
                        return False, "Recipient account not found", rows[0]["balance"], VectorClock.from_json(rows[0]["vector_clock"]), VectorClock()
                    else:
                        return False, "Sender account not found", 0.0, VectorClock(), VectorClock()
                
                # Identify sender and recipient
                sender_row = rows[0] if rows[0]["phone"] == from_phone else rows[1]
                recipient_row = rows[1] if rows[1]["phone"] == to_phone else rows[0]
                
                sender_balance = sender_row["balance"]
                recipient_balance = recipient_row["balance"]
                
                # Check sufficient balance
                new_sender_balance = sender_balance - amount
                if new_sender_balance < 0:
                    return False, "Insufficient balance", sender_balance, VectorClock.from_json(sender_row["vector_clock"]), VectorClock()
                
                new_recipient_balance = recipient_balance + amount
                
                # Get and increment vector clocks
                sender_vc = VectorClock.from_json(sender_row["vector_clock"])
                sender_vc.increment(self.server_id)
                
                recipient_vc = VectorClock.from_json(recipient_row["vector_clock"])
                recipient_vc.increment(self.server_id)
                
                # Update sender account
                self.conn.execute(
                    "UPDATE accounts SET balance = ?, vector_clock = ?, physical_timestamp = ?, last_modified_by = ? WHERE phone = ?",
                    (new_sender_balance, sender_vc.to_json(), time.time(), self.server_id, from_phone)
                )
                
                # Update recipient account
                self.conn.execute(
                    "UPDATE accounts SET balance = ?, vector_clock = ?, physical_timestamp = ?, last_modified_by = ? WHERE phone = ?",
                    (new_recipient_balance, recipient_vc.to_json(), time.time(), self.server_id, to_phone)
                )
                
                # Log sender transaction
                self.conn.execute(
                    "INSERT INTO transactions (phone, type, amount, balance_after, vector_clock, server_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (from_phone, "TRANSFER_OUT", -amount, new_sender_balance, sender_vc.to_json(), self.server_id)
                )
                
                # Log recipient transaction
                self.conn.execute(
                    "INSERT INTO transactions (phone, type, amount, balance_after, vector_clock, server_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (to_phone, "TRANSFER_IN", amount, new_recipient_balance, recipient_vc.to_json(), self.server_id)
                )
                
                self.conn.commit()
                
                return True, "Transfer successful", new_sender_balance, sender_vc, recipient_vc
            except Exception as e:
                self.conn.rollback()
                return False, f"Error: {str(e)}", 0.0, VectorClock(), VectorClock()


class MobileMoneyServer:
    """Main server class"""
    
    def __init__(self, server_id: int):
        self.server_id = server_id
        self.config = config.get_server_by_id(server_id)
        
        if not self.config:
            raise ValueError(f"Server ID {server_id} not found in config")
        
        print(f"[Server {server_id}] Initializing {self.config['name']}...")
        
        # Initialize components
        self.datastore = DataStore(server_id)
        self.wal_manager = WALManager(server_id)
        
        # Sockets
        self.rpc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rep_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # Bind sockets
        self.rpc_socket.bind((self.config['host'], self.config['port']))
        self.rep_socket.bind((self.config['host'], self.config['rep_port']))
        
        # Distributed algorithms
        peer_ids = [s['id'] for s in config.get_active_servers() if s['id'] != server_id]
        self.election = BullyElection(server_id, [server_id] + peer_ids, self._send_to_peer)
        self.clock_sync = BerkeleyClockSync(server_id, self._send_to_peer)
        self.lock_manager = DistributedLockManager(server_id)
        self.two_pc = TwoPhaseCommit(server_id, self._send_to_peer, self.wal_manager)
        self.anti_entropy = AntiEntropy(server_id, self._send_to_peer, lambda: self.datastore.get_all_accounts())
        
        # State
        self.running = False
        self.stats = {
            "requests": 0,
            "replications": 0,
            "elections": 0,
            "clock_syncs": 0,
            "gossips": 0
        }
    
    def _send_to_peer(self, peer_id: int, msg_type: str, data: Dict) -> Optional[Dict]:
        """Send message to peer server"""
        peer_config = config.get_server_by_id(peer_id)
        if not peer_config:
            return None
        
        try:
            message = json.dumps({"type": msg_type, "from": self.server_id, "data": data})
            
            # Send to replication port
            self.rep_socket.sendto(message.encode()[:config.MAX_PACKET_SIZE], 
                                   (peer_config['host'], peer_config['rep_port']))
            
            # Wait for response
            self.rep_socket.settimeout(config.UDP_TIMEOUT_SEC)
            response_data, _ = self.rep_socket.recvfrom(config.MAX_PACKET_SIZE)
            response = json.loads(response_data.decode())
            
            return response.get("data", {})
        except socket.timeout:
            # Silently ignore timeouts (non-critical background tasks)
            return None
        except json.JSONDecodeError:
            # Silently ignore JSON errors (truncated packets)
            return None
        except Exception as e:
            # Only log unexpected errors
            if "timed out" not in str(e).lower():
                print(f"[Server {self.server_id}] Error sending to peer {peer_id}: {e}")
            return None
    
    def start(self):
        """Start the server"""
        print(f"[Server {self.server_id}] Starting on {self.config['host']}:{self.config['port']}...")
        
        # Recover from WAL
        orphaned = self.wal_manager.recover()
        if orphaned:
            print(f"[Server {self.server_id}] Found {len(orphaned)} orphaned transactions, aborting...")
        
        self.running = True
        
        # Start threads
        threading.Thread(target=self._rpc_handler, daemon=True).start()
        threading.Thread(target=self._replication_handler, daemon=True).start()
        threading.Thread(target=self._discovery_service, daemon=True).start()
        
        # Start election
        time.sleep(1)
        print(f"[Server {self.server_id}] Starting election...")
        self.election.start_election()
        
        # Check if database is empty and sync from peers if needed
        threading.Thread(target=self._initial_state_sync, daemon=True).start()
        
        # Background tasks
        threading.Thread(target=self._coordinator_tasks, daemon=True).start()
        threading.Thread(target=self._anti_entropy_task, daemon=True).start()
        
        print(f"[Server {self.server_id}] Ready!")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def _rpc_handler(self):
        """Handle client RPC requests"""
        while self.running:
            try:
                data, addr = self.rpc_socket.recvfrom(config.MAX_PACKET_SIZE)
                threading.Thread(target=self._process_rpc, args=(data, addr), daemon=True).start()
            except Exception as e:
                if self.running:
                    print(f"[Server {self.server_id}] RPC error: {e}")
    
    def _process_rpc(self, data: bytes, addr: Tuple):
        """Process individual RPC request"""
        try:
            message = data.decode().strip()
            parts = message.split('|')
            
            if len(parts) < 3:
                return
            
            req_type, req_id, command = parts[0], parts[1], parts[2]
            args = parts[3:] if len(parts) > 3 else []
            
            self.stats["requests"] += 1
            
            response = ""
            
            if command == "REGISTER":
                phone, pin = args[0], args[1]
                success, msg, vc = self.datastore.create_account(phone, pin)
                
                if success:
                    # Simple direct replication to all peers
                    operation = {"command": "REGISTER", "phone": phone, "pin": pin, "vc": vc.to_json()}
                    self._replicate_to_peers(operation)
                
                balance = 0.0 if success else 0.0
                response = f"RES|{req_id}|{'OK' if success else 'ERR'}|{msg}|{balance}|{vc.to_json()}"
            
            elif command == "BALANCE":
                phone, pin = args[0], args[1]
                
                if not self.datastore.verify_pin(phone, pin):
                    response = f"RES|{req_id}|ERR|Invalid PIN|0.0|{{}}"
                else:
                    account = self.datastore.get_account(phone)
                    if account:
                        response = f"RES|{req_id}|OK|Balance retrieved|{account['balance']}|{account['vector_clock'].to_json()}"
                    else:
                        response = f"RES|{req_id}|ERR|Account not found|0.0|{{}}"
            
            elif command == "DEPOSIT":
                phone, pin, amount = args[0], args[1], float(args[2])
                
                print(f"[Server {self.server_id}] DEPOSIT request: phone={phone}, pin={'*' * len(pin)}, amount={amount}")
                
                if not self.datastore.verify_pin(phone, pin):
                    print(f"[Server {self.server_id}] PIN verification failed for {phone}")
                    response = f"RES|{req_id}|ERR|Invalid PIN|0.0|{{}}"
                else:
                    # Perform atomic deposit operation
                    success, msg, new_balance, vc = self.datastore.atomic_deposit(phone, amount)
                    
                    if success:
                        # Simple direct replication to all peers
                        operation = {"command": "DEPOSIT", "phone": phone, "amount": amount, "vc": vc.to_json()}
                        self._replicate_to_peers(operation)
                    
                    response = f"RES|{req_id}|{'OK' if success else 'ERR'}|{msg}|{new_balance}|{vc.to_json()}"
            
            elif command == "WITHDRAW":
                phone, pin, amount = args[0], args[1], float(args[2])
                
                if not self.datastore.verify_pin(phone, pin):
                    response = f"RES|{req_id}|ERR|Invalid PIN|0.0|{{}}"
                else:
                    # Perform atomic withdraw operation
                    success, msg, new_balance, vc = self.datastore.atomic_withdraw(phone, amount)
                    
                    if success:
                        # Simple direct replication to all peers
                        operation = {"command": "WITHDRAW", "phone": phone, "amount": amount, "vc": vc.to_json()}
                        self._replicate_to_peers(operation)
                    
                    response = f"RES|{req_id}|{'OK' if success else 'ERR'}|{msg}|{new_balance}|{vc.to_json()}"
            
            elif command == "TRANSFER":
                # TRANSFER|from_phone|pin|to_phone|amount
                from_phone, pin, to_phone, amount = args[0], args[1], args[2], float(args[3])
                
                print(f"[Server {self.server_id}] TRANSFER request: from={from_phone} to={to_phone}, amount={amount}")
                
                # Verify sender's PIN
                if not self.datastore.verify_pin(from_phone, pin):
                    print(f"[Server {self.server_id}] PIN verification failed for {from_phone}")
                    response = f"RES|{req_id}|ERR|Invalid PIN|0.0|{{}}"
                else:
                    # Perform atomic transfer operation
                    success, msg, sender_balance, sender_vc, recipient_vc = self.datastore.atomic_transfer(from_phone, to_phone, amount)
                    
                    if success:
                        # Replicate transfer operation
                        operation = {
                            "command": "TRANSFER",
                            "from_phone": from_phone,
                            "to_phone": to_phone,
                            "amount": amount,
                            "sender_vc": sender_vc.to_json(),
                            "recipient_vc": recipient_vc.to_json()
                        }
                        self._replicate_to_peers(operation)
                        
                        print(f"[Server {self.server_id}] Transfer successful: {from_phone} -> {to_phone}, amount={amount}")
                    
                    response = f"RES|{req_id}|{'OK' if success else 'ERR'}|{msg}|{sender_balance}|{sender_vc.to_json()}"
            
            # Send response
            self.rpc_socket.sendto(response.encode()[:config.MAX_PACKET_SIZE], addr)
            
        except Exception as e:
            print(f"[Server {self.server_id}] Error processing RPC: {e}")
    
    def _replicate_to_peers(self, operation: Dict):
        """Simple fire-and-forget replication to all peers"""
        peers = [s for s in config.get_active_servers() if s['id'] != self.server_id]
        
        for peer in peers:
            try:
                message = json.dumps({
                    "type": "REPLICATE",
                    "from": self.server_id,
                    "data": {"operation": operation}
                })
                
                # Send to peer's replication port (fire and forget)
                self.rep_socket.sendto(
                    message.encode()[:config.MAX_PACKET_SIZE],
                    (peer['host'], peer['rep_port'])
                )
            except Exception as e:
                print(f"[Server {self.server_id}] Failed to replicate to server {peer['id']}: {e}")
    
    def _replication_handler(self):
        """Handle replication messages from peers"""
        while self.running:
            try:
                data, addr = self.rep_socket.recvfrom(config.MAX_PACKET_SIZE)
                message = json.loads(data.decode())
                
                msg_type = message.get("type")
                from_server = message.get("from")
                msg_data = message.get("data", {})
                
                response = {"type": f"{msg_type}_RESPONSE", "from": self.server_id, "data": {}}
                
                # Handle different message types
                if msg_type == "REPLICATE":
                    # Apply replicated operation
                    operation = msg_data.get("operation")
                    if operation:
                        self._apply_replicated_operation(operation)
                    # No response needed for fire-and-forget
                    continue
                
                elif msg_type == "ELECT_REQ":
                    response["data"] = self.election.handle_election_request(from_server)
                
                elif msg_type == "ELECT_COORD":
                    self.election.handle_coordinator_message(msg_data.get("coordinator_id"))
                
                elif msg_type == "ELECT_HB":
                    self.election.handle_heartbeat(from_server)
                
                elif msg_type == "CLOCK_REQ":
                    response["data"] = {"time": self.clock_sync.get_time()}
                
                elif msg_type == "CLOCK_ADJ":
                    self.clock_sync.apply_adjustment(msg_data.get("adjustment", 0.0))
                
                elif msg_type == "GOSSIP_MERKLE":
                    local_data = self.datastore.get_all_accounts()
                    local_hashes = {k: MerkleTree.hash_value(str(v)) for k, v in local_data.items()}
                    response["data"] = {"data_hashes": local_hashes}
                
                elif msg_type == "STATE_REQUEST":
                    # Handle full state request from a new/empty server
                    print(f"[Server {self.server_id}] Received state request from Server {from_server}")
                    
                    # Get all accounts with full details
                    accounts = {}
                    with self.datastore.lock:
                        cursor = self.datastore.conn.execute(
                            "SELECT phone, pin, balance, vector_clock, physical_timestamp, last_modified_by FROM accounts"
                        )
                        for row in cursor.fetchall():
                            accounts[row[0]] = {
                                "pin": row[1],
                                "balance": row[2],
                                "vector_clock": row[3],
                                "physical_timestamp": row[4],
                                "last_modified_by": row[5]
                            }
                    
                    # Serialize accounts to JSON
                    accounts_json = json.dumps(accounts)
                    data_size = len(accounts_json.encode())
                    
                    # Check if data needs to be chunked
                    if data_size > config.CHUNK_SIZE:
                        # Split into chunks
                        chunks = []
                        for i in range(0, len(accounts_json), config.CHUNK_SIZE):
                            chunks.append(accounts_json[i:i + config.CHUNK_SIZE])
                        
                        # Store chunks for later retrieval
                        if not hasattr(self, '_state_chunks'):
                            self._state_chunks = {}
                        self._state_chunks[from_server] = chunks
                        
                        # Send first chunk with metadata
                        response["data"] = {
                            "chunked": True,
                            "total_chunks": len(chunks),
                            "data": chunks[0],
                            "total_size": data_size
                        }
                        print(f"[Server {self.server_id}] Sending {len(accounts)} account(s) to Server {from_server} in {len(chunks)} chunks ({data_size} bytes)")
                    else:
                        # Send all data in one response
                        response["data"] = {"accounts": accounts}
                        print(f"[Server {self.server_id}] Sending {len(accounts)} account(s) to Server {from_server} ({data_size} bytes)")
                
                elif msg_type == "STATE_REQUEST_CHUNK":
                    # Handle chunk request
                    chunk_id = msg_data.get("chunk_id", 0)
                    
                    if hasattr(self, '_state_chunks') and from_server in self._state_chunks:
                        chunks = self._state_chunks[from_server]
                        if chunk_id < len(chunks):
                            response["data"] = {
                                "success": True,
                                "data": chunks[chunk_id],
                                "chunk_id": chunk_id
                            }
                            print(f"[Server {self.server_id}] Sending chunk {chunk_id + 1}/{len(chunks)} to Server {from_server}")
                        else:
                            response["data"] = {"success": False, "error": "Invalid chunk ID"}
                    else:
                        response["data"] = {"success": False, "error": "No chunks available"}
                
                # Send response (skip for REPLICATE which has no response)
                if msg_type != "REPLICATE":
                    response_data = json.dumps(response).encode()
                    # Send in chunks if needed
                    if len(response_data) > config.MAX_PACKET_SIZE:
                        # Truncate to max size (shouldn't happen with chunking, but safety check)
                        response_data = response_data[:config.MAX_PACKET_SIZE]
                    self.rep_socket.sendto(response_data, addr)
                
            except json.JSONDecodeError as e:
                # Silently ignore JSON errors from truncated packets (non-critical)
                pass
            except socket.timeout:
                # Silently ignore timeouts (non-critical background tasks)
                pass
            except Exception as e:
                if self.running:
                    # Only log unexpected errors
                    if "timed out" not in str(e).lower():
                        print(f"[Server {self.server_id}] Replication error: {e}")
    
    def _discovery_service(self):
        """Handle server discovery broadcasts"""
        discovery_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        discovery_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        discovery_sock.bind(('', config.DISCOVERY_PORT))
        
        while self.running:
            try:
                data, addr = discovery_sock.recvfrom(config.MAX_PACKET_SIZE)
                message = data.decode().strip()
                
                if message == "DISCOVER":
                    # Respond with server info
                    response = json.dumps({
                        "id": self.server_id,
                        "name": self.config['name'],
                        "host": self.config['host'],
                        "port": self.config['port'],
                        "load": self.stats["requests"]
                    })
                    discovery_sock.sendto(response.encode(), addr)
            except Exception as e:
                if self.running:
                    print(f"[Server {self.server_id}] Discovery error: {e}")
    
    def _coordinator_tasks(self):
        """Background tasks for coordinator"""
        while self.running:
            time.sleep(1)
            
            if self.election.is_coordinator():
                # Send heartbeats
                if int(time.time()) % int(config.COORDINATOR_HEARTBEAT_SEC) == 0:
                    peers = [s['id'] for s in config.get_active_servers() if s['id'] != self.server_id]
                    for peer_id in peers:
                        self._send_to_peer(peer_id, "ELECT_HB", {})
                
                # Clock sync
                if int(time.time()) % int(config.CLOCK_SYNC_INTERVAL_SEC) == 0:
                    peers = [s['id'] for s in config.get_active_servers() if s['id'] != self.server_id]
                    self.clock_sync.sync_clocks(peers)
                    self.stats["clock_syncs"] += 1
                
                # Cleanup expired locks
                self.lock_manager.cleanup_expired_locks()
            else:
                # Check if coordinator is alive
                if not self.election.check_coordinator_alive(config.COORDINATOR_TIMEOUT_SEC):
                    print(f"[Server {self.server_id}] Coordinator timeout, starting election...")
                    self.election.start_election()
                    self.stats["elections"] += 1
    
    def _anti_entropy_task(self):
        """Background anti-entropy/gossip"""
        while self.running:
            time.sleep(config.GOSSIP_INTERVAL_SEC)
            
            peers = [s['id'] for s in config.get_active_servers() if s['id'] != self.server_id]
            if peers:
                peer_id = random.choice(peers)
                result = self.anti_entropy.gossip_with_peer(peer_id)
                self.stats["gossips"] += 1
                
                if result.get("synced", 0) > 0:
                    print(f"[Server {self.server_id}] Gossip with {peer_id}: {result['synced']} differences")
    
    def _initial_state_sync(self):
        """Sync state from peers on startup if database is empty or has differences"""
        # Wait for server to be fully initialized and for peers to be ready
        time.sleep(5)  # Increased from 3 to 5 seconds to ensure peers are ready
        
        # Check if database is empty
        account_count = 0
        with self.datastore.lock:
            cursor = self.datastore.conn.execute("SELECT COUNT(*) FROM accounts")
            account_count = cursor.fetchone()[0]
        
        if account_count == 0:
            print(f"[Server {self.server_id}] Database is empty, requesting full state from peers...")
            self._sync_full_state_from_peers()
        else:
            print(f"[Server {self.server_id}] Database has {account_count} account(s), checking for differences...")
            self._sync_differences_from_peers()
    
    def _sync_full_state_from_peers(self):
        """Sync full state when database is completely empty"""
        # Get list of peers
        peers = [s['id'] for s in config.get_active_servers() if s['id'] != self.server_id]
        
        if not peers:
            print(f"[Server {self.server_id}] No peers available for state sync")
            return
        
        # Try to get state from each peer until successful
        for peer_id in peers:
            print(f"[Server {self.server_id}] Requesting full state from Server {peer_id}...")
            
            result = self.anti_entropy.request_full_state(peer_id)
            
            if result.get("success"):
                accounts = result.get("accounts", {})
                synced_count = 0
                
                print(f"[Server {self.server_id}] Received {len(accounts)} account(s) from Server {peer_id}")
                
                # Insert each account into local database
                for phone, account_data in accounts.items():
                    try:
                        with self.datastore.lock:
                            # Check if account already exists
                            cursor = self.datastore.conn.execute(
                                "SELECT phone FROM accounts WHERE phone = ?", (phone,)
                            )
                            if cursor.fetchone():
                                continue
                            
                            # Insert account
                            self.datastore.conn.execute(
                                "INSERT INTO accounts (phone, pin, balance, vector_clock, physical_timestamp, last_modified_by) VALUES (?, ?, ?, ?, ?, ?)",
                                (
                                    phone,
                                    account_data.get("pin", ""),
                                    account_data.get("balance", 0.0),
                                    account_data.get("vector_clock", "{}"),
                                    account_data.get("physical_timestamp", time.time()),
                                    account_data.get("last_modified_by", peer_id)
                                )
                            )
                            self.datastore.conn.commit()
                            synced_count += 1
                    except Exception as e:
                        print(f"[Server {self.server_id}] Error syncing account {phone}: {e}")
                
                print(f"[Server {self.server_id}] ✓ Initial state sync complete: {synced_count} account(s) synced from Server {peer_id}")
                return
            else:
                print(f"[Server {self.server_id}] Failed to get state from Server {peer_id}: {result.get('error', 'Unknown error')}")
        
        print(f"[Server {self.server_id}] ⚠ Could not sync state from any peer")
    
    def _sync_differences_from_peers(self):
        """Sync differences when database has data but might be out of sync"""
        # Get list of peers
        peers = [s['id'] for s in config.get_active_servers() if s['id'] != self.server_id]
        
        if not peers:
            print(f"[Server {self.server_id}] No peers available for difference sync")
            return
        
        # Get local accounts
        local_accounts = {}
        with self.datastore.lock:
            cursor = self.datastore.conn.execute(
                "SELECT phone, balance, vector_clock, physical_timestamp FROM accounts"
            )
            for row in cursor.fetchall():
                local_accounts[row[0]] = {
                    "balance": row[1],
                    "vector_clock": row[2],
                    "physical_timestamp": row[3]
                }
        
        # Try to sync with each peer (with retries)
        total_synced = 0
        for peer_id in peers:
            print(f"[Server {self.server_id}] Checking differences with Server {peer_id}...")
            
            # Retry up to 3 times
            result = None
            for attempt in range(3):
                result = self.anti_entropy.request_full_state(peer_id)
                
                if result.get("success"):
                    break
                else:
                    if attempt < 2:
                        print(f"[Server {self.server_id}] Retry {attempt + 1}/3 for Server {peer_id}...")
                        time.sleep(2)  # Wait before retry
            
            if not result or not result.get("success"):
                error_msg = result.get("error", "Unknown error") if result else "No response"
                print(f"[Server {self.server_id}] Failed to check differences with Server {peer_id}: {error_msg}")
                continue
            
            peer_accounts = result.get("accounts", {})
            print(f"[Server {self.server_id}] Received {len(peer_accounts)} account(s) from Server {peer_id}")
            
            # Find accounts that exist on peer but not locally
            missing_accounts = []
            for phone, peer_data in peer_accounts.items():
                if phone not in local_accounts:
                    missing_accounts.append(phone)
            
            # Find accounts with different balances
            different_accounts = []
            for phone, peer_data in peer_accounts.items():
                if phone in local_accounts:
                    local_balance = local_accounts[phone]["balance"]
                    peer_balance = peer_data.get("balance", 0.0)
                    if local_balance != peer_balance:
                        # Compare vector clocks to determine which is newer
                        local_vc = VectorClock.from_json(local_accounts[phone]["vector_clock"])
                        peer_vc = VectorClock.from_json(peer_data.get("vector_clock", "{}"))
                        comparison = local_vc.compare(peer_vc)
                        
                        if comparison == "before":
                            # Peer has newer data
                            different_accounts.append((phone, "peer_newer"))
                        elif comparison == "concurrent":
                            # Concurrent updates - use Last-Writer-Wins
                            local_ts = local_accounts[phone].get("physical_timestamp", 0)
                            peer_ts = peer_data.get("physical_timestamp", 0)
                            if peer_ts > local_ts:
                                different_accounts.append((phone, "peer_newer"))
            
            if missing_accounts:
                print(f"[Server {self.server_id}] Found {len(missing_accounts)} missing account(s)")
                
                # Sync missing accounts
                for phone in missing_accounts:
                    peer_data = peer_accounts[phone]
                    try:
                        with self.datastore.lock:
                            self.datastore.conn.execute(
                                "INSERT INTO accounts (phone, pin, balance, vector_clock, physical_timestamp, last_modified_by) VALUES (?, ?, ?, ?, ?, ?)",
                                (
                                    phone,
                                    peer_data.get("pin", ""),
                                    peer_data.get("balance", 0.0),
                                    peer_data.get("vector_clock", "{}"),
                                    peer_data.get("physical_timestamp", time.time()),
                                    peer_data.get("last_modified_by", peer_id)
                                )
                            )
                            self.datastore.conn.commit()
                            total_synced += 1
                            print(f"[Server {self.server_id}]   ✓ Synced missing account: {phone} (balance={peer_data.get('balance', 0.0)})")
                    except Exception as e:
                        print(f"[Server {self.server_id}]   ✗ Error syncing account {phone}: {e}")
            
            if different_accounts:
                print(f"[Server {self.server_id}] Found {len(different_accounts)} account(s) with different data")
                
                # Update accounts where peer has newer data
                for phone, reason in different_accounts:
                    peer_data = peer_accounts[phone]
                    try:
                        with self.datastore.lock:
                            self.datastore.conn.execute(
                                "UPDATE accounts SET balance = ?, vector_clock = ?, physical_timestamp = ?, last_modified_by = ? WHERE phone = ?",
                                (
                                    peer_data.get("balance", 0.0),
                                    peer_data.get("vector_clock", "{}"),
                                    peer_data.get("physical_timestamp", time.time()),
                                    peer_data.get("last_modified_by", peer_id),
                                    phone
                                )
                            )
                            self.datastore.conn.commit()
                            total_synced += 1
                            print(f"[Server {self.server_id}]   ✓ Updated account {phone}: balance={peer_data.get('balance', 0.0)}")
                    except Exception as e:
                        print(f"[Server {self.server_id}]   ✗ Error updating account {phone}: {e}")
            
            if not missing_accounts and not different_accounts:
                print(f"[Server {self.server_id}] ✓ No differences found with Server {peer_id}")
        
        if total_synced > 0:
            print(f"[Server {self.server_id}] ✓ Difference sync complete: {total_synced} account(s) synced/updated")
        else:
            print(f"[Server {self.server_id}] ✓ All accounts are in sync")
    
    def _apply_replicated_operation(self, operation: Dict):
        """Apply a replicated operation from another server"""
        try:
            command = operation.get("command")
            
            if command == "REGISTER":
                phone = operation.get("phone")
                pin = operation.get("pin")
                vc = VectorClock.from_json(operation.get("vc", "{}"))
                
                # Check if account already exists
                existing = self.datastore.get_account(phone)
                if not existing:
                    # Create account directly in database
                    with self.datastore.lock:
                        self.datastore.conn.execute(
                            "INSERT INTO accounts (phone, pin, balance, vector_clock, physical_timestamp, last_modified_by) VALUES (?, ?, ?, ?, ?, ?)",
                            (phone, pin, 0.0, vc.to_json(), time.time(), operation.get("server_id", 0))
                        )
                        self.datastore.conn.commit()
                    print(f"[Server {self.server_id}] Replicated REGISTER for {phone}")
            
            elif command == "DEPOSIT":
                phone = operation.get("phone")
                amount = operation.get("amount")
                vc = VectorClock.from_json(operation.get("vc", "{}"))
                
                account = self.datastore.get_account(phone)
                if account:
                    self.datastore.update_balance(phone, amount, "DEPOSIT", vc)
                    print(f"[Server {self.server_id}] Replicated DEPOSIT for {phone}: {amount}")
            
            elif command == "WITHDRAW":
                phone = operation.get("phone")
                amount = operation.get("amount")
                vc = VectorClock.from_json(operation.get("vc", "{}"))
                
                account = self.datastore.get_account(phone)
                if account:
                    self.datastore.update_balance(phone, -amount, "WITHDRAW", vc)
                    print(f"[Server {self.server_id}] Replicated WITHDRAW for {phone}: {amount}")
            
            elif command == "TRANSFER":
                from_phone = operation.get("from_phone")
                to_phone = operation.get("to_phone")
                amount = operation.get("amount")
                sender_vc = VectorClock.from_json(operation.get("sender_vc", "{}"))
                recipient_vc = VectorClock.from_json(operation.get("recipient_vc", "{}"))
                
                # Apply both parts of the transfer
                sender = self.datastore.get_account(from_phone)
                recipient = self.datastore.get_account(to_phone)
                
                if sender and recipient:
                    self.datastore.update_balance(from_phone, -amount, "TRANSFER_OUT", sender_vc)
                    self.datastore.update_balance(to_phone, amount, "TRANSFER_IN", recipient_vc)
                    print(f"[Server {self.server_id}] Replicated TRANSFER: {from_phone} -> {to_phone}, amount={amount}")
            
            elif command == "SYNC_ACCOUNT":
                # Network sync operation - insert or update account
                phone = operation.get("phone")
                pin = operation.get("pin")
                balance = operation.get("balance", 0.0)
                vector_clock = operation.get("vector_clock", "{}")
                physical_timestamp = operation.get("physical_timestamp", time.time())
                last_modified_by = operation.get("last_modified_by", 0)
                
                # Check if account exists
                existing = self.datastore.get_account(phone)
                
                with self.datastore.lock:
                    if existing:
                        # Update if newer
                        existing_ts = existing.get("physical_timestamp", 0)
                        if physical_timestamp >= existing_ts:
                            self.datastore.conn.execute(
                                "UPDATE accounts SET pin = ?, balance = ?, vector_clock = ?, physical_timestamp = ?, last_modified_by = ? WHERE phone = ?",
                                (pin, balance, vector_clock, physical_timestamp, last_modified_by, phone)
                            )
                            self.datastore.conn.commit()
                            print(f"[Server {self.server_id}] Network sync: Updated {phone} (balance={balance})")
                    else:
                        # Insert new account
                        self.datastore.conn.execute(
                            "INSERT INTO accounts (phone, pin, balance, vector_clock, physical_timestamp, last_modified_by) VALUES (?, ?, ?, ?, ?, ?)",
                            (phone, pin, balance, vector_clock, physical_timestamp, last_modified_by)
                        )
                        self.datastore.conn.commit()
                        print(f"[Server {self.server_id}] Network sync: Added {phone} (balance={balance})")
        
        except Exception as e:
            print(f"[Server {self.server_id}] Error applying replicated operation: {e}")
    
    def stop(self):
        """Stop the server"""
        print(f"\n[Server {self.server_id}] Shutting down...")
        self.running = False
        self.rpc_socket.close()
        self.rep_socket.close()
        self.discovery_socket.close()
        self.datastore.conn.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python server.py <server_id>")
        print("Example: python server.py 1")
        sys.exit(1)
    
    server_id = int(sys.argv[1])
    server = MobileMoneyServer(server_id)
    server.start()


if __name__ == "__main__":
    main()
