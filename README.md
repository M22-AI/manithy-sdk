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
| **Python 3.8+** | Compatible with Python 3.8 and above. |

## Installation

```bash
pip install manithy-sdk
```

Or install from source:

```bash
git clone https://github.com/VooYee/manithy-sdk.git
cd manithy-sdk
pip install .
```

## Quick Start

```python
from manithy import ManithySDK

sdk = ManithySDK()

result = sdk.capture(
    context={"actor": "user-42", "action": "approve_payment", "resource": "invoice-1001"},
    snapshot={"amount": 250.00, "currency": "USD", "recipient": "Acme Corp"},
)

print(result)
# {"status": "CAPTURED", "id": "a3f8c9..."}
```

Output (stdout):

```
MANITHY_PROOF::{"spec":"1.0","id":"<sha256>","meta":{"ts":"2026-02-10T...","actor":"user-42","action":"approve_payment","resource":"invoice-1001"},"data":{"amount":250,"currency":"USD","recipient":"Acme Corp"}}
```

### `context` vs `snapshot`

| Parameter | Purpose | Example |
|---|---|---|
| **`context`** | *Who* did *what* to *which resource*. Metadata describing the event. Not hashed — only stored in the envelope's `meta` block. | `{"actor": "user-42", "action": "approve_payment", "resource": "invoice-1001"}` |
| **`snapshot`** | *The data itself* at the moment of capture. This is what gets canonicalized and hashed into the `commit_id`. If even one byte changes, the hash changes. | `{"amount": 250.00, "currency": "USD", "recipient": "Acme Corp"}` |

Think of **context** as the *label on the envelope* (who sent it, when, why) and **snapshot** as the *contents inside* (the actual evidence being sealed).

## Custom Buffer

Route proofs to a file, queue, or any destination by subclassing `CaptureBuffer`:

```python
import json
from manithy import ManithySDK
from manithy.interfaces.buffer import CaptureBuffer

class FileBuffer(CaptureBuffer):
    def __init__(self, path: str):
        self._file = open(path, "a", encoding="utf-8")

    def emit(self, envelope: dict) -> None:
        self._file.write(json.dumps(envelope, separators=(",", ":")) + "\n")
        self._file.flush()

sdk = ManithySDK(buffer=FileBuffer("audit.log"))
```

## Configuration

### Kill-Switch

Disable all capture at runtime without code changes:

```bash
export MANITHY_ENABLED=false   # Linux/macOS
```

```powershell
$env:MANITHY_ENABLED = "false"  # Windows PowerShell
```

When disabled, `capture()` returns `{"status": "SKIPPED"}` immediately.

### Debug Mode

Log internal SDK errors to stderr (useful during development):

```bash
export MANITHY_DEBUG=true
```

## How It Works

1. **Kill-switch check** — reads `MANITHY_ENABLED`. If `"false"`, returns `SKIPPED`.
2. **Canonicalization** — normalizes the snapshot into deterministic bytes (sorted keys, no whitespace, floats like `100.0` → `100`).
3. **Hashing** — computes SHA-256 of the canonical bytes → 64-char hex `commit_id`.
4. **Envelope assembly** — wraps commit-ID, context, snapshot, and UTC timestamp into a proof record.
5. **Emit** — writes the envelope to the configured buffer (default: stdout with `MANITHY_PROOF::` prefix).

If any step fails, the error is swallowed and `{"status": "ERROR", "error": "Internal SDK Error"}` is returned. The host application is **never** affected.

## Development

```bash
# Create a virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\Activate.ps1       # Windows PowerShell

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

## Project Structure

```
src/manithy/
├── __init__.py      # Public API: exposes ManithySDK
├── sdk.py           # Main entry point (capture pipeline + fail-closed)
├── config.py        # Environment variable loader (kill-switch + debug)
├── core/
│   ├── canonical.py # Deterministic JSON canonicalization
│   ├── hasher.py    # SHA-256 commit-ID generation
│   └── envelope.py  # Proof envelope assembly (spec v1.0)
└── interfaces/
    └── buffer.py    # Abstract CaptureBuffer + StdoutBuffer
tests/
├── vectors.json     # Golden test vectors (canonical + hash)
├── test_core.py     # Core module tests (canonical, hasher, envelope)
└── test_sdk.py      # SDK integration tests (capture, kill-switch, fail-closed)
```
