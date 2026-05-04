#!/bin/bash
# Start all configured servers in localhost mode

echo "Starting Distributed Mobile Money Servers..."
echo "=============================================="

# Create data directory
mkdir -p data
mkdir -p wal

# Start each server in background
python server.py 1 &
SERVER1_PID=$!
echo "Started Server 1 (PID: $SERVER1_PID)"

sleep 1

python server.py 2 &
SERVER2_PID=$!
echo "Started Server 2 (PID: $SERVER2_PID)"

sleep 1

python server.py 3 &
SERVER3_PID=$!
echo "Started Server 3 (PID: $SERVER3_PID)"

echo ""
echo "All servers started!"
echo "=============================================="
echo "Server PIDs: $SERVER1_PID, $SERVER2_PID, $SERVER3_PID"
echo ""
echo "To stop servers, run: ./stop_servers.sh"
echo "To view logs, check terminal output"
echo "To run client: python client.py"
echo ""

# Save PIDs to file for stop script
echo "$SERVER1_PID" > .server_pids
echo "$SERVER2_PID" >> .server_pids
echo "$SERVER3_PID" >> .server_pids

# Wait for all servers
wait
