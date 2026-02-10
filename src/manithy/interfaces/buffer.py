"""
manithy.interfaces.buffer
~~~~~~~~~~~~~~~~~~~~~~~~~~

Capture Buffer — Abstract Base & Default Stdout Implementation.

A ``CaptureBuffer`` defines *where* proof envelopes are sent after they
are constructed.  The SDK ships with a single concrete implementation
(``StdoutBuffer``) that prints envelopes to stdout.  Consumers can
subclass ``CaptureBuffer`` to route proofs to files, queues, or
external collectors — **as long as the implementation itself does not
violate the Zero-Network-I/O constraint** during the synchronous
``emit()`` call.

Owner: [Dev B]

Output Format (StdoutBuffer)
-----------------------------
Each emitted envelope is printed as a **single line** to stdout with
the following prefix::

    MANITHY_PROOF::{"spec":"1.0","id":"<hex>","meta":{...},"data":{...}}

The prefix allows downstream log processors (Fluentd, Datadog, etc.)
to grep/filter audit proofs from regular application logs.
"""

from __future__ import annotations

import abc
from typing import Any


class CaptureBuffer(abc.ABC):
    """Abstract base class for proof-envelope output buffers.

    Subclasses must implement the ``emit`` method.
    """

    @abc.abstractmethod
    def emit(self, envelope: dict[str, Any]) -> None:
        """Emit a proof envelope to the underlying transport.

        Parameters
        ----------
        envelope : dict[str, Any]
            The fully constructed Manithy proof envelope.
        """
        ...


class StdoutBuffer(CaptureBuffer):
    """Default buffer that prints proof envelopes to stdout.

    Output is a single line per envelope, prefixed with
    ``MANITHY_PROOF::`` followed by the compact JSON representation
    (no extra whitespace).

    Implementation Notes (TODO)
    ---------------------------
    1. Serialize *envelope* to compact JSON using
       ``json.dumps(envelope, separators=(',', ':'))``.
    2. Print ``f"MANITHY_PROOF::{json_str}"`` to stdout via ``print()``.
    """

    def emit(self, envelope: dict[str, Any]) -> None:
        """Print the envelope to stdout with the ``MANITHY_PROOF::`` prefix.

        Parameters
        ----------
        envelope : dict[str, Any]
            The proof envelope to emit.
        """
        # TODO: Serialize envelope to compact JSON and print with prefix.
        pass
