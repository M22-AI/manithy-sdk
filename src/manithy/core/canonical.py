"""
manithy.core.canonical
~~~~~~~~~~~~~~~~~~~~~~

Deterministic JSON Canonicalization.

This module converts an arbitrary Python data structure (dicts, lists,
primitives) into a **canonical byte string** that is identical across
Python and Node.js for the same logical input.

Owner: [Dev A]

Cross-Language Determinism Rules
--------------------------------
1. **Sort object keys** — recursively, at every nesting level, using
   standard lexicographic (Unicode code-point) order.

2. **Strip insignificant whitespace** — the output must contain no
  spaces or newlines between tokens (equivalent to
  ``json.dumps(separators=(',', ':'))``).

3. **Normalize numbers** —
   * Floats that are mathematically integers (e.g. ``100.0``, ``3.0``)
     **must** be emitted as integers (``100``, ``3``) so the byte output
    matches what ``JSON.stringify`` produces in Node.js.
   * Non-integer floats (e.g. ``3.14``) should be serialized with full
    precision, avoiding trailing zeros.

4. **Encoding** — the final output must be UTF-8 encoded ``bytes``.

5. **No external libraries** — only ``json`` from the standard library.

Example
-------
>>> to_canonical_bytes({"b": 1, "a": [3.0, {"d": 4, "c": 5}]})
b'{"a":[3,{"c":5,"d":4}],"b":1}'
"""

from __future__ import annotations

import json
from typing import Any


def _normalize(data: Any, _seen: set) -> Any:
    """Recursively normalize *data* for deterministic serialization.

    - Sorts dict keys lexicographically.
    - Converts whole-number floats to ints (the "float trap").
    - Detects circular references via object-id tracking.
    """
    obj_id = id(data)
    if isinstance(data, (dict, list)):
        if obj_id in _seen:
            raise ValueError("Circular reference detected")
        _seen.add(obj_id)

    if isinstance(data, dict):
        result = {k: _normalize(v, _seen) for k, v in sorted(data.items())}
        _seen.discard(obj_id)
        return result

    if isinstance(data, list):
        result = [_normalize(item, _seen) for item in data]
        _seen.discard(obj_id)
        return result

    if isinstance(data, float):
        if data.is_integer():
            return int(data)
        return data

    return data


def to_canonical_bytes(data: Any) -> bytes:
    """Convert *data* to deterministic, canonical UTF-8 JSON bytes.

    Parameters
    ----------
    data : Any
        Arbitrary JSON-serializable Python object (dict, list, str,
        int, float, bool, None).

    Returns
    -------
    bytes
        UTF-8 encoded canonical JSON with sorted keys, no whitespace,
        and floats-that-are-integers coerced to ints.

    Raises
    ------
    TypeError
        If *data* contains types that are not JSON-serializable.
    ValueError
        If *data* contains circular references.
    """
    normalized = _normalize(data, set())
    return json.dumps(normalized, separators=(",", ":"), sort_keys=False).encode("utf-8")
