# NomaanOS GhostNode

An experimental air-gapped peer coordination prototype for disconnected environments.

## Status

This repository is a research prototype for local peer coordination and offline workload patterns. It is not a production-ready distributed system and should not be treated as one without independent validation.

## What it does

GhostNode explores:

- local peer communication patterns
- air-gapped or disconnected mesh experimentation
- keyed verification patterns for trusted local coordination
- resilience and partial connectivity behavior in constrained environments

## Quick start

```bash
git clone https://github.com/NomaanOS-Dev/NomaanOS-GhostNode.git
cd NomaanOS-GhostNode
python3 -m venv .venv
source .venv/bin/activate
python ghost_core.py
```

## Important notes

- coordination behavior depends heavily on network topology and device assumptions
- air-gapped peer models are experimental and not production-proven
- real deployment requires environment-specific validation and protocol review
