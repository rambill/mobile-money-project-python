#!/usr/bin/env python3
"""
Mobile-Friendly Web Client for Mobile Money System
Access from any phone browser
"""

from flask import Flask, render_template, request, jsonify, session
import socket
import time
import json
import secrets
from typing import Dict, Optional

import config

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

class WebMobileMoneyClient:
    """Web-based mobile money client"""
    
    def __init__(self):
        self.servers = self.discover_servers()
    
    def discover_servers(self):
        """Discover servers from config"""
        servers = []
        
        for server in config.get_active_servers():
            # Try to ping server
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(1.0)
                
                req_id = f"ping_{time.time()}"
                message = f"REQ|{req_id}|BALANCE|0000000000|0000"
                
                start = time.time()
                sock.sendto(message.encode(), (server['host'], server['port']))
                
                data, addr = sock.recvfrom(config.MAX_PACKET_SIZE)
                latency = (time.time() - start) * 1000
                
                sock.close()
                
                servers.append({
                    "id": server['id'],
                    "name": server['name'],
                    "host": server['host'],
                    "port": server['port'],
                    "latency": latency
                })
            except:
                pass
        
        return servers
    
    def send_request(self, server_id: int, command: str, *args) -> Optional[Dict]:
        """Send request to server"""
        server = next((s for s in self.servers if s['id'] == server_id), None)
        if not server:
            return {"success": False, "error": "Server not found"}
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5.0)
            
            req_id = f"web_{time.time()}"
            message = f"REQ|{req_id}|{command}|" + "|".join(str(arg) for arg in args)
            
            sock.sendto(message.encode(), (server['host'], server['port']))
            
            data, addr = sock.recvfrom(config.MAX_PACKET_SIZE)
            response = data.decode().strip()
            
            sock.close()
            
            # Parse response: RES|req_id|status|message|balance|vector_clock
            parts = response.split('|')
            if len(parts) >= 4:
                status = parts[2]
                message = parts[3]
                balance = float(parts[4]) if len(parts) > 4 else 0.0
                
                return {
                    "success": status == "OK",
                    "message": message,
                    "balance": balance
                }
            
            return {"success": False, "error": "Invalid response"}
            
        except socket.timeout:
            return {"success": False, "error": "Request timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}


client = WebMobileMoneyClient()


@app.route('/')
def index():
    """Main page"""
    return render_template('mobile.html', servers=client.servers)


@app.route('/api/servers')
def get_servers():
    """Get list of servers"""
    return jsonify({"servers": client.servers})


@app.route('/api/register', methods=['POST'])
def register():
    """Register new account"""
    data = request.json
    phone = data.get('phone')
    pin = data.get('pin')
    server_id = data.get('server_id', 1)
    
    if not phone or not pin:
        return jsonify({"success": False, "error": "Phone and PIN required"})
    
    result = client.send_request(server_id, "REGISTER", phone, pin)
    
    if result.get("success"):
        session['phone'] = phone
        session['pin'] = pin
        session['server_id'] = server_id
    
    return jsonify(result)


@app.route('/api/login', methods=['POST'])
def login():
    """Login to account"""
    data = request.json
    phone = data.get('phone')
    pin = data.get('pin')
    server_id = data.get('server_id', 1)
    
    if not phone or not pin:
        return jsonify({"success": False, "error": "Phone and PIN required"})
    
    result = client.send_request(server_id, "BALANCE", phone, pin)
    
    if result.get("success"):
        session['phone'] = phone
        session['pin'] = pin
        session['server_id'] = server_id
    
    return jsonify(result)


@app.route('/api/balance', methods=['GET'])
def balance():
    """Check balance"""
    phone = session.get('phone')
    pin = session.get('pin')
    server_id = session.get('server_id', 1)
    
    if not phone or not pin:
        return jsonify({"success": False, "error": "Not logged in"})
    
    result = client.send_request(server_id, "BALANCE", phone, pin)
    return jsonify(result)


@app.route('/api/deposit', methods=['POST'])
def deposit():
    """Deposit money"""
    phone = session.get('phone')
    pin = session.get('pin')
    server_id = session.get('server_id', 1)
    
    if not phone or not pin:
        return jsonify({"success": False, "error": "Not logged in"})
    
    data = request.json
    amount = data.get('amount')
    
    if not amount or amount <= 0:
        return jsonify({"success": False, "error": "Invalid amount"})
    
    result = client.send_request(server_id, "DEPOSIT", phone, pin, amount)
    return jsonify(result)


@app.route('/api/withdraw', methods=['POST'])
def withdraw():
    """Withdraw money"""
    phone = session.get('phone')
    pin = session.get('pin')
    server_id = session.get('server_id', 1)
    
    if not phone or not pin:
        return jsonify({"success": False, "error": "Not logged in"})
    
    data = request.json
    amount = data.get('amount')
    
    if not amount or amount <= 0:
        return jsonify({"success": False, "error": "Invalid amount"})
    
    result = client.send_request(server_id, "WITHDRAW", phone, pin, amount)
    return jsonify(result)


@app.route('/api/transfer', methods=['POST'])
def transfer():
    """Transfer money"""
    phone = session.get('phone')
    pin = session.get('pin')
    server_id = session.get('server_id', 1)
    
    if not phone or not pin:
        return jsonify({"success": False, "error": "Not logged in"})
    
    data = request.json
    to_phone = data.get('to_phone')
    amount = data.get('amount')
    
    if not to_phone or not amount or amount <= 0:
        return jsonify({"success": False, "error": "Invalid transfer details"})
    
    result = client.send_request(server_id, "TRANSFER", phone, pin, to_phone, amount)
    return jsonify(result)


@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout"""
    session.clear()
    return jsonify({"success": True})


if __name__ == '__main__':
    print("=" * 60)
    print("MOBILE MONEY WEB CLIENT")
    print("=" * 60)
    print("\nStarting web server...")
    print(f"\nAccess from your phone:")
    print(f"  http://<your-pc-ip>:8000")
    print(f"\nExample:")
    print(f"  http://10.29.42.224:8000")
    print("\n" + "=" * 60)
    
    app.run(host='0.0.0.0', port=8000, debug=True)
