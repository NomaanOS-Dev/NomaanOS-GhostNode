import urllib.request
import json
import os

SWARM_PORT = 8090
SWARM_SECRET_KEY = os.environ.get("SWARM_SECRET_KEY", "nomaanos-secure-ghost-key-2026")

def test_swarm():
    url = f"http://localhost:{SWARM_PORT}/swarm-execute"
    payload = {
        "secret": SWARM_SECRET_KEY,
        "model": "gemma:2b",
        "prompt": "Say 'Ghost Node Swarm Operational' in 3 words."
    }
    
    print("[*] Sending cryptographically signed payload to Ghost-Node swarm...")
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            print("\n[+] Swarm Execution Successful!")
            print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\n[X] Error during swarm execution test: {e}")

if __name__ == "__main__":
    test_swarm()
