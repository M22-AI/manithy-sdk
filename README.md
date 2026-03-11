# Manithy SDK (Python)

**Authority-Grade Audit Capture — Zero Dependencies**

Manithy captures tamper-evident audit proofs at the application layer.
Each proof is a **J01 CommitBoundaryEvent** — a structured record that
marks the exact t-1 boundary before an irreversible action and freezes
only facts already resolved in the execution context.

No lookups. No inference. No enrichment.

## Design Constraints

| Constraint | Guarantee |
|---|---|
| **Zero Network I/O** | The SDK never opens sockets or makes HTTP calls. |
| **Determinism** | Identical inputs always yield identical commit-IDs. |
| **Fail-Closed** | Internal errors are silently swallowed — the host app never crashes. |
| **Zero Dependencies** | Only the Python standard library is used at runtime. |
| **Epistemic Honesty** | The `availability` block declares what was knowable at t-1. Unknown facts must never appear in `observed`. |

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
    boundary_kind="REFUND_COMMIT_T_MINUS_1",
    boundary_seq=1,
    tenant_id="FINANCE_DESK",
    action_class="TRADE_EXECUTION",
    commit_point_id="REFUND_COMMIT_T_MINUS_1",
    auth_metadata={
        "auth_subject": "TRADER_005",
        "auth_provider": "AUTH_LAYER_V1",
    },
    same_thread=True,
    observed={
        "action_kind": "REFUND",
        "amount_minor": 12900,
        "currency": "EUR",
        "refund_mode": "FULL",
        "order_channel": "WEB",
        "payment_method": "CARD",
        "merchant_region": "EU",
        "customer_present": False,
        "operator_initiated": False,
    },
    availability={
        "psp_refund_capability_known": True,
        "original_payment_state_known": True,
        "chargeback_state_known": False,
    },
    reentrancy_guard="SINGLE_CAPTURE_ENFORCED",
)

print(result)
# {"status": "CAPTURED", "id": "a3f8c9..."}
```

Output (stdout):

```
MANITHY_PROOF::{"kind":"J01.CommitBoundaryEvent","schema_id":"manithy.commit_boundary_event.v2","commit_seq":1,"meta":{"tenant_id":"FINANCE_DESK","action_class":"TRADE_EXECUTION","commit_point_id":"REFUND_COMMIT_T_MINUS_1","auth_subject":"TRADER_005","auth_provider":"AUTH_LAYER_V1"},"boundary":{"boundary_kind":"REFUND_COMMIT_T_MINUS_1","boundary_seq":1,"same_thread":true,"reentrancy_guard":"SINGLE_CAPTURE_ENFORCED"},"adapter_snapshot":{"observed":{...},"availability":{...}},"commit_id":"a3f8c9..."}
```

Legacy v1 output can still be requested:

```python
sdk.capture(..., schema_version="v1")
```

## Capture Parameters

| Parameter | Type | Purpose |
|---|---|---|
| **`boundary_kind`** | `str` | Which irreversible boundary this event refers to. Consumer-defined closed enum (e.g. `"REFUND_COMMIT_T_MINUS_1"`). |
| **`boundary_seq`** | `int` | Supports rare cases of multiple irreversible calls in one execution path. Small integer (0–255). |
| **`tenant_id`** | `str \| None` | Tenant identifier captured in the v2 `meta` block. |
| **`action_class`** | `str \| None` | Domain action category captured in v2 `meta` (for example: `"TRADE_EXECUTION"`). |
| **`commit_point_id`** | `str \| None` | Stable business checkpoint ID captured in v2 `meta`, usually equal to `boundary_kind`. |
| **`auth_metadata`** | `dict[str, Any] \| None` | Additional authentication-layer metadata merged into v2 `meta`. |
| **`same_thread`** | `bool` | Runtime assertion that capture happened same-thread at t-1. |
| **`observed`** | `dict[str, str\|int\|bool]` | Runtime facts already resolved in the execution context. Values must be primitives only — no floats, no `None`, no nested structures. |
| **`availability`** | `dict[str, bool]` | Epistemic visibility at t-1. Each key declares whether a fact was knowable before the irreversible action. |
| **`reentrancy_guard`** | `str` | Capture enforcement mode. Consumer-defined (e.g. `"SINGLE_CAPTURE_ENFORCED"`). |
| **`schema_version`** | `str` | Envelope schema version. Default `"v2"`; use `"v1"` for backward compatibility. |

### The `observed` Block

All fields in `observed` must already be resolved in the execution context at t-1.

**Allowed:** `str`, `int`, `bool`.
**Forbidden:** `float`, `None`, nested `dict`/`list`, any value fetched or inferred after execution.

### The `availability` Block

`availability` is not data. It is a **declaration of epistemic visibility** at t-1.

Each key answers one question:
> "At the exact moment before the irreversible action, was this fact already knowable inside the execution context — yes or no?"

| `_known` value | Meaning | Effect |
|---|---|---|
| `True` | Fact was knowable at t-1 | May appear in `observed` |
| `False` | Fact was NOT knowable at t-1 | Must NOT appear in `observed` |

If the fact was not knowable, Manithy records **ignorance**, not a value.
That ignorance is structural and permanent.

### Forbidden Fields

The following fields must **never** appear in a CommitBoundaryEvent:

| Field | Why Forbidden |
|---|---|
| `callsite_id` | High joinability risk. |
| `producer_build_id` | Belongs in PackInit / EvidencePack provenance, not J01. |
| `producer_invocation_id` | High joinability risk. Single-capture is enforced via guard state, not IDs. |

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
2. **Validation** — enforces type constraints on all fields; rejects forbidden fields, floats in `observed`, non-bool in `availability`, and unknown facts that leak into `observed`.
3. **Event assembly** — builds a J01 `CommitBoundaryEvent` with schema `manithy.commit_boundary_event.v2` by default (or `v1` when `schema_version="v1"`).
4. **Hashing** — canonicalizes the event (sorted keys, no whitespace, floats like `100.0` → `100`) and computes SHA-256 → 64-char hex `commit_id`.
5. **Emit** — writes the event to the configured buffer (default: stdout with `MANITHY_PROOF::` prefix). For v2, `commit_id` is embedded into the emitted envelope.

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
│   └── envelope.py  # J01 CommitBoundaryEvent assembly + validation
└── interfaces/
    └── buffer.py    # Abstract CaptureBuffer + StdoutBuffer
tests/
├── vectors.json     # Golden test vectors (canonical + hash)
├── test_core.py     # Core module tests (canonical, hasher, J01 event)
└── test_sdk.py      # SDK integration tests (capture, kill-switch, fail-closed)
```
