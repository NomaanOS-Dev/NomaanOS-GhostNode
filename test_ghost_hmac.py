import json
import time
import uuid
import threading
import urllib.request
import pytest
from ghost_core import run_server, compute_hmac_signature, SWARM_PORT, SWARM_SECRET_KEY

# Background server starter
@pytest.fixture(scope="session", autouse=True)
def start_ghost_server():
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(0.5)

def send_payload(payload):
    url = f"http://localhost:{SWARM_PORT}/swarm-execute"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def test_valid_hmac_request():
    now = time.time()
    nonce = str(uuid.uuid4())
    prompt = "Status verify"
    sig = compute_hmac_signature(SWARM_SECRET_KEY, now, nonce, prompt)
    
    payload = {
        "timestamp": now,
        "nonce": nonce,
        "prompt": prompt,
        "signature": sig
    }
    status, res = send_payload(payload)
    assert status == 200
    assert "response" in res

def test_tampered_signature_blocked():
    now = time.time()
    nonce = str(uuid.uuid4())
    prompt = "Malicious command execution"
    
    payload = {
        "timestamp": now,
        "nonce": nonce,
        "prompt": prompt,
        "signature": "deadbeef" * 8
    }
    status, res = send_payload(payload)
    assert status == 403
    assert "Unauthorized" in res["error"]

def test_replay_attack_blocked():
    now = time.time()
    nonce = str(uuid.uuid4())
    prompt = "Replay target"
    sig = compute_hmac_signature(SWARM_SECRET_KEY, now, nonce, prompt)
    
    payload = {
        "timestamp": now,
        "nonce": nonce,
        "prompt": prompt,
        "signature": sig
    }
    # First attempt: Pass
    status1, _ = send_payload(payload)
    assert status1 == 200
    
    # Replay attempt: Must Block
    status2, res2 = send_payload(payload)
    assert status2 == 403
    assert "Unauthorized" in res2["error"]

def test_expired_timestamp_blocked():
    expired_time = time.time() - 300.0  # 5 minutes old
    nonce = str(uuid.uuid4())
    prompt = "Old timestamp payload"
    sig = compute_hmac_signature(SWARM_SECRET_KEY, expired_time, nonce, prompt)
    
    payload = {
        "timestamp": expired_time,
        "nonce": nonce,
        "prompt": prompt,
        "signature": sig
    }
    status, res = send_payload(payload)
    assert status == 403
