"""
manithy.core.envelope
~~~~~~~~~~~~~~~~~~~~~

Proof-Envelope Assembly.

A proof envelope is the self-contained JSON structure that constitutes
a single Manithy audit proof.  It wraps together the commit-ID, the
capture context, and the snapshot data along with standard metadata.

Owner: [Dev A]

Envelope Schema (spec "1.0")
-----------------------------
{
    "spec": "1.0",
    "id":   "<commit_id>",
    "meta": {
        "ts":  "<ISO-8601 UTC timestamp>",
        ...context fields...
    },
    "data": { ...snapshot... }
}

Constraints
-----------
* The ``meta.ts`` timestamp must be generated at call time using
  ``datetime.datetime.now(datetime.timezone.utc).isoformat()``.
* ``context`` is an arbitrary dict of caller-supplied metadata
  (e.g. ``actor``, ``action``, ``resource``).  Its contents are merged
  into ``meta``.
* This function is **pure** except for the timestamp side-effect.
"""

from __future__ import annotations

from typing import Any


def build_envelope(
    commit_id: str,
    context: dict[str, Any],
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    """Construct a Manithy proof envelope dictionary.

    Parameters
    ----------
    commit_id : str
        The SHA-256 commit-ID (64-char hex string) identifying this
        proof.
    context : dict[str, Any]
        Caller-supplied metadata (actor, action, resource, etc.).
        Merged into the ``meta`` block alongside the timestamp.
    snapshot : dict[str, Any]
        The data payload being captured as proof.

    Returns
    -------
    dict[str, Any]
        A dictionary with four top-level keys:

        * ``spec`` — always ``"1.0"``.
        * ``id``   — the *commit_id*.
        * ``meta`` — ``{"ts": "<ISO-8601>", **context}``.
        * ``data`` — the *snapshot*.

    Implementation Notes (TODO)
    ---------------------------
    1. Generate an ISO-8601 UTC timestamp string.
    2. Build the ``meta`` dict by merging ``{"ts": ts}`` with *context*.
    3. Return ``{"spec": "1.0", "id": commit_id, "meta": meta,
       "data": snapshot}``.
    """
    # TODO: Implement envelope construction.
    pass
