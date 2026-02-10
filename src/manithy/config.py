"""
manithy.config
~~~~~~~~~~~~~~

Runtime Configuration & Kill-Switch.

The SDK's behaviour can be controlled at runtime through environment
variables.  This keeps the SDK inert in environments where audit
capture should be suppressed (e.g. unit-test runners, CI pipelines)
without requiring code changes.

Owner: [Dev B]

Environment Variables
---------------------
``MANITHY_ENABLED``
    Set to ``"false"`` (case-insensitive) to disable all capture.
    Any other value (or absence of the variable) means **enabled**.
    Default: ``True`` (enabled).
"""

from __future__ import annotations


def is_enabled() -> bool:
    """Return whether the Manithy SDK is enabled.

    Reads the ``MANITHY_ENABLED`` environment variable via
    ``os.environ``.

    * If the variable is **absent** → return ``True`` (enabled by
      default).
    * If the variable is set to ``"false"`` (case-insensitive) →
      return ``False``.
    * Any other value → return ``True``.

    Returns
    -------
    bool
        ``True`` if capture should proceed, ``False`` otherwise.

    Implementation Notes (TODO)
    ---------------------------
    1. ``import os``
    2. ``raw = os.environ.get("MANITHY_ENABLED", "true")``
    3. ``return raw.strip().lower() != "false"``
    """
    # TODO: Implement environment-variable check.
    pass
