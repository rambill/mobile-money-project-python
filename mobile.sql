-- Database Schema for Distributed Mobile Money System

-- Accounts table with vector clock
CREATE TABLE IF NOT EXISTS accounts (
    phone TEXT PRIMARY KEY,
    pin TEXT NOT NULL,
    balance REAL DEFAULT 0.0,
    vector_clock TEXT DEFAULT '{}',  -- JSON: {server_id: counter}
    physical_timestamp REAL,
    last_modified_by INTEGER,
    created_at REAL DEFAULT (julianday('now'))
);

-- Transactions log
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL,
    type TEXT NOT NULL,  -- DEPOSIT, WITHDRAW, TRANSFER_OUT, TRANSFER_IN
    amount REAL NOT NULL,
    balance_after REAL NOT NULL,
    timestamp REAL DEFAULT (julianday('now')),
    vector_clock TEXT,
    server_id INTEGER,
    FOREIGN KEY (phone) REFERENCES accounts(phone)
);

-- Replication log for exactly-once delivery
CREATE TABLE IF NOT EXISTS replication_log (
    seq_num INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL,  -- JSON of operation
    vector_clock TEXT NOT NULL,
    physical_timestamp REAL NOT NULL,
    server_id INTEGER NOT NULL,
    applied BOOLEAN DEFAULT 0,
    applied_at REAL
);

-- Server registry for peer tracking
CREATE TABLE IF NOT EXISTS server_registry (
    server_id INTEGER PRIMARY KEY,
    name TEXT,
    host TEXT,
    port INTEGER,
    rep_port INTEGER,
    last_seen REAL,
    is_coordinator BOOLEAN DEFAULT 0,
    vector_clock TEXT DEFAULT '{}'
);

-- Cache table for server-side caching
CREATE TABLE IF NOT EXISTS cache (
    key TEXT PRIMARY KEY,
    value TEXT,
    expires_at REAL
);

-- Write-Ahead Log for 2PC
CREATE TABLE IF NOT EXISTS wal_2pc (
    txn_id TEXT PRIMARY KEY,
    operation TEXT NOT NULL,
    state TEXT NOT NULL,  -- PREPARE, COMMIT, ABORT
    timestamp REAL DEFAULT (julianday('now')),
    participants TEXT  -- JSON array of server IDs
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_transactions_phone ON transactions(phone);
CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_replication_log_applied ON replication_log(applied);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at);
