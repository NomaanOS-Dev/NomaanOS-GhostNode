import os
import sys
import json
import socket
import logging
import threading
import urllib.request
import urllib.error
import hmac
import hashlib
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

# --- CONFIGURATION & LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [GHOST-V8-ENGINE] %(message)s"
)

SWARM_PORT = 8090
DISCOVERY_PORT = 8091
SWARM_SECRET_KEY = os.environ.get("SWARM_SECRET_KEY", "nomaanos-secure-ghost-key-2026")
LOCAL_NODE_ID = socket.gethostname()

class ClusterRegistry:
    def __init__(self):
        self.peers = {}
        self.lock = threading.Lock()

    def update_node(self, node_id, addr):
        with self.lock:
            self.peers[node_id] = {"addr": addr, "last_seen": time.time()}

    def cleanup_dead_nodes(self, timeout=15):
        while True:
            time.sleep(5)
            now = time.time()
            with self.lock:
                dead = [nid for nid, info in self.peers.items() if now - info["last_seen"] > timeout]
                for nid in dead:
                    logging.info(f"Node timed out and dropped from cluster registry: {nid}")
                    del self.peers[nid]

cluster_registry = ClusterRegistry()

# --- UDP BROADCAST & DISCOVERY ---
def broadcast_presence():
    """Silently broadcasts node presence to local network via UDP with proper socket flags."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    message = json.dumps({"node_id": LOCAL_NODE_ID, "port": SWARM_PORT}).encode('utf-8')
    
    while True:
        try:
            sock.sendto(message, ('<broadcast>', DISCOVERY_PORT))
        except Exception as e:
            # Suppress routine broadcast network restrictions on restricted interfaces
            pass
        time.sleep(3)

def listen_for_peers(registry):
    """Listens for active peer heartbeats on the discovery port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(('', DISCOVERY_PORT))
    except Exception as e:
        logging.error(f"Failed to bind discovery listener: {e}")
        return

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            packet = json.loads(data.decode('utf-8'))
            node_id = packet.get("node_id")
            if node_id and node_id != LOCAL_NODE_ID:
                registry.update_node(node_id, addr[0])
        except Exception:
            pass

# --- HTTP SWARM REQUEST HANDLER ---
class ProductionSwarmHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/swarm-execute':
            try:
                length = int(self.headers.get('Content-Length', 0))
                req_data = json.loads(self.rfile.read(length).decode('utf-8'))

                # Cryptographic token validation via HMAC comparison
                client_secret = req_data.get("secret", "")
                if not hmac.compare_digest(client_secret, SWARM_SECRET_KEY):
                    self.send_response(403)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Unauthorized Swarm Node Access"}).encode('utf-8'))
                    return

                prompt = req_data.get('prompt', '')
                model = req_data.get('model', 'gemma:2b')

                logging.info(f"Executing distributed inference query for model '{model}': {prompt[:30]}...")

                # Forward query locally to the Ollama daemon
                ollama_payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode('utf-8')
                req = urllib.request.Request(
                    "http://localhost:11434/api/generate",
                    data=ollama_payload,
                    headers={'Content-Type': 'application/json'}
                )

                with urllib.request.urlopen(req, timeout=60) as resp:
                    res_json = json.loads(resp.read().decode('utf-8'))
                    ai_response = res_json.get("response", "").strip()

                response_payload = {
                    "status": "success",
                    "node_source": LOCAL_NODE_ID,
                    "response": ai_response
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_payload).encode('utf-8'))

            except Exception as e:
                logging.error(f"Inference pipeline execution error: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Override default HTTP logging to keep stdout pristine
        return

class CustomTCPServer(socketserver.TCPServer):
    allow_reuse_address = True  # Instantly frees port on restart (Prevents Errno 98 Address already in use)

def run_swarm_server(registry):
    # Background threads for resilient cluster discovery & node garbage collection
    threading.Thread(target=broadcast_presence, daemon=True).start()
    threading.Thread(target=listen_for_peers, args=(registry,), daemon=True).start()
    threading.Thread(target=registry.cleanup_dead_nodes, daemon=True).start()

    logging.info(f"Node synchronized & authenticated in cluster: {LOCAL_NODE_ID} (127.0.0.1)")
    
    with CustomTCPServer(("", SWARM_PORT), ProductionSwarmHandler) as httpd:
        logging.info(f"Production Ghost-Node Swarm Daemon secured and listening on port {SWARM_PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logging.info("Shutting down Ghost-Node Swarm Daemon safely...")
            httpd.server_close()

if __name__ == "__main__":
    run_swarm_server(cluster_registry)
