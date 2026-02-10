# Manithy SDK (Python)

**Authority-Grade Audit Capture — Zero Dependencies**

Manithy captures tamper-evident audit proofs at the application layer.
Each proof is a deterministic, content-addressed JSON envelope that can
be independently verified across Python and Node.js runtimes.

## Design Constraints

| Constraint | Guarantee |
|---|---|
| **Zero Network I/O** | The SDK never opens sockets or makes HTTP calls. |
| **Determinism** | Identical inputs always yield identical commit-IDs. |
| **Fail-Closed** | Internal errors are silently swallowed — the host app never crashes. |
| **Zero Dependencies** | Only the Python standard library is used at runtime. |

## Quick Start

```python
from manithy import ManithySDK

sdk = ManithySDK()

envelope = sdk.capture(
    context={"actor": "user-42", "action": "approve"},
    snapshot={"amount": 100.0, "currency": "USD"},
)
```

Output (stdout):

```
MANITHY_PROOF::{"spec":"1.0","id":"<sha256>","meta":{...},"data":{...}}
```

## Kill-Switch

Set the environment variable to disable capture at runtime:

```bash
export MANITHY_ENABLED=false
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Project Structure

```
src/manithy/
├── sdk.py           # Main entry point (capture pipeline + fail-closed)
├── config.py        # Environment variable loader (kill-switch)
├── core/
│   ├── canonical.py # Deterministic JSON canonicalization
│   ├── hasher.py    # SHA-256 commit-ID generation
│   └── envelope.py  # Proof envelope assembly (spec v1.0)
└── interfaces/
    └── buffer.py    # Stdout buffer (MANITHY_PROOF:: prefix)
```

## Ownership

- **Dev A (The Mathematician)** — `core/` module: canonical, hasher, envelope, golden vectors
- **Dev B (The Guardian)** — `sdk.py`, `config.py`, `interfaces/`, build config, tests
