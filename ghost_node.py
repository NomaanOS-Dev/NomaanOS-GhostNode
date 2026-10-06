import hashlib
import hmac
import secrets
import time
from typing import Dict


class GhostNodeEngine:
    """Local node identity and keyed challenge proof.

    The proof is an HMAC, not hardware-backed attestation. Protect the key and
    use a nonce supplied by a verifier to reduce replay risk.
    """

    def __init__(self, node_id: str, attestation_key: bytes) -> None:
        if not node_id or not node_id.strip():
            raise ValueError("node_id must be non-empty")
        if not isinstance(attestation_key, bytes) or len(attestation_key) < 32:
            raise ValueError("attestation_key must contain at least 32 bytes")
        self.node_id = node_id
        self.status = "ACTIVE_AIR_GAPPED"
        self.timestamp = time.time()
        self._attestation_key = attestation_key

    def generate_attestation_proof(self, challenge: str) -> Dict[str, str]:
        if not challenge or not challenge.strip():
            raise ValueError("challenge must be non-empty")
        message = f"{challenge}:{self.node_id}:{self.status}:{self.timestamp}".encode()
        signature = hmac.new(self._attestation_key, message, hashlib.sha256).hexdigest()
        return {
            "node_id": self.node_id,
            "challenge": challenge,
            "issued_at": str(self.timestamp),
            "proof": signature,
        }


if __name__ == "__main__":
    node = GhostNodeEngine("node-alpha-01", secrets.token_bytes(32))
    print("GhostNode Initialized:", node.generate_attestation_proof("local-demo"))
