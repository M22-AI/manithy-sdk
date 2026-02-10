"""
Manithy SDK — Authority-Grade Audit Capture
============================================

Public API surface:
    from manithy import ManithySDK

Constraints:
    - Zero Network I/O   → The SDK never opens sockets or makes HTTP calls.
    - Determinism         → Identical inputs always yield identical outputs.
    - Fail-Closed         → Any internal error is silently swallowed; the host
                            application must never crash because of the SDK.
"""

from manithy.sdk import ManithySDK  # noqa: F401

__all__ = ["ManithySDK"]
