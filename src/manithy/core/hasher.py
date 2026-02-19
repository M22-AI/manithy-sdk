"""
manithy.core.hasher
~~~~~~~~~~~~~~~~~~~

Deterministic Commit-ID Generation.

A commit-ID is the **SHA-256 hex digest** of the canonical byte
representation of a data payload.  Because the canonical form is
deterministic (see ``canonical.py``), the commit-ID is also
deterministic — identical logical data always yields the same ID,
regardless of key insertion order or float formatting.

Owner: [Dev A]

Constraints
-----------
* Use **only** ``hashlib`` from the standard library.
* The output must be a **lowercase hex string** (64 characters).
* This function is **pure** — no side-effects, no I/O.
"""

from __future__ import annotations

import hashlib
from typing import Any

from manithy.core.canonical import to_canonical_bytes


def generate_commit_id(data: Any) -> str:
    """Return the SHA-256 hex digest of *data*'s canonical byte form.

    Parameters
    ----------
    data : Any
        The JSON-serializable payload to hash.

    Returns
    -------
    str
        A 64-character lowercase hexadecimal SHA-256 digest string.
    """
    canonical_bytes = to_canonical_bytes(data)
    return hashlib.sha256(canonical_bytes).hexdigest()
