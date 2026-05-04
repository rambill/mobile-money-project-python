#!/bin/bash
# Stop all running servers

echo "Stopping Distributed Mobile Money Servers..."
echo "=============================================="

if [ -f .server_pids ]; then
    while read pid; do
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping server (PID: $pid)"
            kill $pid
        else
            echo "Server (PID: $pid) not running"
        fi
    done < .server_pids
    
    rm .server_pids
    echo ""
    echo "All servers stopped!"
else
    echo "No PID file found. Trying to find Python server processes..."
    
    # Find and kill server processes
    pkill -f "python.*server.py"
    
    echo "Done!"
fi

echo "=============================================="
