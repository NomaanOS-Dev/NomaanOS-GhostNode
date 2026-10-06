# NomaanOS-GhostNode

Prototype identity and attestation primitives for local, air-gapped NomaanOS nodes.

## Current implementation

- Validates node identity and a minimum-length secret key.
- Produces a keyed HMAC proof bound to a caller-provided challenge, node ID, status, and issue time.
- Makes no claim of hardware-backed attestation, encrypted transport, peer discovery, consensus, or complete air-gap security.

The verifier must retain the shared key, validate the challenge, enforce an expiry window, and reject reused challenges. In production, prefer device-backed keys and a documented key rotation/revocation process.

## Roadmap (not implemented)

- [ ] Mesh peer discovery with cryptographic handshakes
- [ ] Encrypted payload routing over local interfaces
- [ ] Swarm consensus and leader election
- [ ] Hardware-backed key storage
- [ ] Signed and timestamped attestations

## Run

```bash
python ghost_node.py
