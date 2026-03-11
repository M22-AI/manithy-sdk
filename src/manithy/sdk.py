"""
manithy.sdk
~~~~~~~~~~~

Main Entry Point — ``ManithySDK``.

This is the **only** class that application developers interact with.
It orchestrates the full capture pipeline:

    1. Check the kill-switch (``config.is_enabled``).
    2. Validate & build the J01 CommitBoundaryEvent.
    3. Hash the observed block to produce a commit-ID.
    4. Emit the event through the configured buffer.

Owner: [Dev B]

Design Principles
-----------------
* **Fail-Closed** — the ``capture`` method wraps its *entire* body in a
    global ``try / except Exception``.  If anything goes wrong the error
    is silently swallowed (optionally logged to stderr) and the host
    application is **never** affected.

* **Zero Network I/O** — the SDK never opens sockets.  Output goes to
    a local ``CaptureBuffer`` (default: stdout).

* **Determinism** — identical ``observed`` payloads produce identical
    commit-IDs.

* **Epistemic Honesty** — the ``availability`` block declares what was
    knowable at t-1.  Unknown facts must never appear in ``observed``.
"""

from __future__ import annotations

from typing import Any

from manithy.config import is_debug, is_enabled
from manithy.core.envelope import build_commit_boundary_event
from manithy.core.hasher import generate_commit_id
from manithy.interfaces.buffer import CaptureBuffer, StdoutBuffer


class ManithySDK:
    """Authority-Grade Audit Capture SDK.

    Parameters
    ----------
    buffer : CaptureBuffer | None
        The output buffer used to emit proof envelopes.  Defaults to
        ``StdoutBuffer()`` which prints to stdout.

    Usage
    -----
    >>> sdk = ManithySDK()
    >>> sdk.capture(
    ...     boundary_kind="REFUND_COMMIT_T_MINUS_1",
    ...     boundary_seq=1,
    ...     same_thread=True,
    ...     observed={
    ...         "action_kind": "REFUND",
    ...         "amount_minor": 12900,
    ...         "currency": "EUR",
    ...     },
    ...     availability={
    ...         "psp_refund_capability_known": True,
    ...         "original_payment_state_known": True,
    ...         "chargeback_state_known": False,
    ...     },
    ...     reentrancy_guard="SINGLE_CAPTURE_ENFORCED",
    ... )
    """

    def __init__(self, buffer: CaptureBuffer | None = None) -> None:
        self._buffer = buffer or StdoutBuffer()

    def capture(
        self,
        boundary_kind: str,
        boundary_seq: int,
        same_thread: bool,
        observed: dict[str, Any],
        availability: dict[str, bool],
        reentrancy_guard: str,
        tenant_id: str | None = None,
        action_class: str | None = None,
        commit_point_id: str | None = None,
        auth_metadata: dict[str, Any] | None = None,
        schema_version: str = "v2",
    ) -> dict[str, Any] | None:
        """Capture a J01 CommitBoundaryEvent.

        Marks the exact t-1 boundary before an irreversible action and
        records only facts already resolved in the execution context.

        Parameters
        ----------
        boundary_kind : str
            Which irreversible boundary this event refers to.
            The valid values are defined by the SDK consumer.
        boundary_seq : int
            Sequence number for multiple irreversible calls in one path.
        same_thread : bool
            Assertion that capture happened same-thread at t-1.
        observed : dict[str, Any]
            Runtime facts already resolved (primitives only).
        availability : dict[str, bool]
            Epistemic visibility at t-1.
        reentrancy_guard : str
            Capture enforcement mode.  Defined by the SDK consumer.

        Returns
        -------
        dict[str, Any] | None
            A status dict on success/skip/error.
        """
        if not is_enabled():
            return {"status": "SKIPPED"}

        try:
            event = build_commit_boundary_event(
                boundary_kind=boundary_kind,
                boundary_seq=boundary_seq,
                same_thread=same_thread,
                observed=observed,
                availability=availability,
                reentrancy_guard=reentrancy_guard,
                tenant_id=tenant_id,
                action_class=action_class,
                commit_point_id=commit_point_id,
                auth_metadata=auth_metadata,
                schema_version=schema_version,
            )
            commit_id = generate_commit_id(event)
            if schema_version == "v2":
                event["commit_id"] = commit_id
            self._buffer.emit(event)
            return {"status": "CAPTURED", "id": commit_id}
        except Exception as exc:
            if is_debug():
                import sys

                print(f"[ManithySDK] {exc}", file=sys.stderr)
            return {"status": "ERROR", "error": "Internal SDK Error"}
