"""
manithy.sdk
~~~~~~~~~~~

Main Entry Point — ``ManithySDK``.

This is the **only** class that application developers interact with.
It orchestrates the full capture pipeline:

    1. Check the kill-switch (``config.is_enabled``).
    2. Hash the snapshot to produce a commit-ID.
    3. Build the proof envelope.
    4. Emit the envelope through the configured buffer.

Owner: [Dev B]

Design Principles
-----------------
* **Fail-Closed** — the ``capture`` method wraps its *entire* body in a
  global ``try / except Exception``.  If anything goes wrong the error
  is silently swallowed (optionally logged to stderr) and the host
  application is **never** affected.

* **Zero Network I/O** — the SDK never opens sockets.  Output goes to
  a local ``CaptureBuffer`` (default: stdout).

* **Determinism** — identical ``(context, snapshot)`` pairs produce
  identical commit-IDs (though the envelope timestamp will differ).
"""

from __future__ import annotations

from typing import Any

from manithy.config import is_enabled
from manithy.core.envelope import build_envelope
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
    ...     context={"actor": "user-42", "action": "approve"},
    ...     snapshot={"amount": 100.0, "currency": "USD"},
    ... )

    Implementation Notes (TODO)
    ---------------------------
    * Store the *buffer* (or default to ``StdoutBuffer()``) in
      ``self._buffer``.
    """

    def __init__(self, buffer: CaptureBuffer | None = None) -> None:
        # TODO: Initialize self._buffer (default to StdoutBuffer).
        pass

    def capture(
        self,
        context: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Capture an audit proof for the given *snapshot*.

        Parameters
        ----------
        context : dict[str, Any]
            Metadata describing the event (actor, action, resource …).
        snapshot : dict[str, Any]
            The data payload to be hashed and recorded.

        Returns
        -------
        dict[str, Any] | None
            The proof envelope on success, or ``None`` if the SDK is
            disabled or an error occurs.

        CRITICAL Implementation Notes (TODO)
        -------------------------------------
        1. **Global Try-Catch** — wrap the ENTIRE body in::

               try:
                   ...
               except Exception:
                   return None

           The host application must **never** crash because of us.

        2. **Kill-Switch** — call ``is_enabled()`` first.  If it
           returns ``False``, return ``None`` immediately.

        3. **Pipeline** —
           a. ``commit_id = generate_commit_id(snapshot)``
           b. ``envelope  = build_envelope(commit_id, context, snapshot)``
           c. ``self._buffer.emit(envelope)``
           d. ``return envelope``
        """
        # TODO: Implement the capture pipeline with fail-closed guard.
        pass
