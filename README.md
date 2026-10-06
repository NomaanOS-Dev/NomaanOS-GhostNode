# 🛰️ NomaanOS GhostNode — Air-Gapped Swarm Engine
> **A decentralized, cryptographic peer-to-peer compute node designed to execute AI workloads across isolated, offline devices without internet connectivity.**

---

### 💡 What is GhostNode? (In 10 Seconds)
Standard multi-agent systems rely on centralized cloud APIs like OpenAI or AWS. **GhostNode enables zero-trust device meshes**:
- **Air-Gapped Operation**: Connects local machines over ad-hoc local sockets, Wi-Fi Direct, or local LANs without any internet access.
- **Cryptographic Node Proofs**: Nodes verify payloads using keyed HMAC signatures before execution.
- **Fault-Tolerant Engine**: If one peer node disconnects, tasks gracefully failover across surviving active nodes.

---

## 🏗️ Swarm Topology

```text
  [ Edge Node A ] <--- Keyed HMAC Verification ---> [ Edge Node B ]
   (Local Socket)                                    (Local Socket)
          \                                                /
           \                                              /
            +-----> [ Ghost Core Engine (`ghost_core.py`) ] <-----+
                                   |
                     Zero-Trust Local Workload
                                   |
                       [ Verified Output Log ]

🚀 Quickstart & Testing
​Run the node listener and client test suite locally:
​1. Launch the Ghost Core Listener
python ghost_core.py

2. Run the Verification Client
​In a separate terminal or background session:
python test_client.py

🛡️ Repository Structure
FileDescription
ghost_core.pyMain P2P daemon, socket handler, and payload verification engine.
test_client.pyTest harness simulating peer handshakes and secure task dispatching.
ghost_node.pyLightweight runtime configuration stub for edge deployments.
