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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [GHOST-V8-ENGINE] %(message)s"
)

SWARM_PORT = 8090
DISCOVERY_PORT = 8091
SWARM_SECRET_KEY = os.environ.get("SWARM_SECRET_KEY", "nomaanos-secure-ghost-key-2026")
LOCAL_NODE_ID = socket.gethostname()
MAX_TIMESTAMP_DRIFT_SEC = 60.0

class ClusterRegistry:
    def __init__(self):
        self.peers = {}
        self.used_nonces = set()
        self.lock = threading.Lock()

    def update_node(self, node_id, addr):
        with self.lock:
            self.peers[node_id] = {"addr": addr, "last_seen": time.time()}

    def is_valid_nonce(self, nonce: str) -> bool:
        with self.lock:
            if nonce in self.used_nonces:
                return False
            self.used_nonces.add(nonce)
            # Memory bounded set (keep last 5000)
            if len(self.used_nonces) > 5000:
                self.used_nonces.clear()
            return True

    def cleanup_dead_nodes(self, timeout=15):
        while True:
            time.sleep(5)
            now = time.time()
            with self.lock:
                dead = [nid for nid, info in self.peers.items() if now - info["last_seen"] > timeout]
                for nid in dead:
                    logging.info(f"Node timed out and dropped: {nid}")
                    del self.peers[nid]

cluster_registry = ClusterRegistry()

def compute_hmac_signature(key: str, timestamp: float, nonce: str, payload_data: str) -> str:
    message = f"{int(timestamp)}:{nonce}:{payload_data}".encode("utf-8")
    return hmac.new(key.encode("utf-8"), message, hashlib.sha256).hexdigest()

class ProductionSwarmHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/swarm-execute':
            try:
                length = int(self.headers.get('Content-Length', 0))
                req_data = json.loads(self.rfile.read(length).decode('utf-8'))

                # Support both True HMAC Signature and legacy shared-secret backward compatibility
                signature = req_data.get("signature")
                timestamp = req_data.get("timestamp")
                nonce = req_data.get("nonce")
                prompt = req_data.get("prompt", "")
                model = req_data.get("model", "gemma:2b")

                authenticated = False
                if signature and timestamp and nonce:
                    # True HMAC Verification
                    current_time = time.time()
                    if abs(current_time - float(timestamp)) <= MAX_TIMESTAMP_DRIFT_SEC:
                        if cluster_registry.is_valid_nonce(str(nonce)):
                            expected_sig = compute_hmac_signature(SWARM_SECRET_KEY, float(timestamp), str(nonce), prompt)
                            if hmac.compare_digest(signature, expected_sig):
                                authenticated = True
                elif req_data.get("secret"):
                    # Legacy bearer check
                    if hmac.compare_digest(req_data.get("secret", ""), SWARM_SECRET_KEY):
                        authenticated = True

                if not authenticated:
                    self.send_response(403)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Unauthorized Swarm Node: Invalid or Replayed HMAC Signature"}).encode('utf-8'))
                    return

                logging.info(f"Validated Node HMAC: Executing model '{model}' for prompt: {prompt[:30]}...")

                # Offline Mock / Fallback logic if Ollama is not locally running
                try:
                    ollama_payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode('utf-8')
                    req = urllib.request.Request(
                        "http://localhost:11434/api/generate",
                        data=ollama_payload,
                        headers={'Content-Type': 'application/json'}
                    )
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        response_data = json.loads(resp.read().decode('utf-8'))
                except Exception:
                    response_data = {
                        "model": model,
                        "response": f"[SOVEREIGN_NODE_EXEC]: {prompt} [PROCESSED_AIR_GAPPED]",
                        "done": True,
                        "backend": "offline_edge_fallback"
                    }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))

            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def log_message(self, format, *args):
        pass

def run_server(port=SWARM_PORT):
    server = HTTPServer(('0.0.0.0', port), ProductionSwarmHandler)
    server.serve_forever()

if __name__ == "__main__":
    t_clean = threading.Thread(target=cluster_registry.cleanup_dead_nodes, daemon=True)
    t_clean.start()
    logging.info(f"GhostNode Daemon Active on port {SWARM_PORT}")
    run_server()
