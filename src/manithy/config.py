from __future__ import annotations

import os


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
    """
    raw = os.environ.get("MANITHY_ENABLED", "true")
    return raw.strip().lower() != "false"


def is_debug() -> bool:
    """Return whether debug mode is enabled.

    Reads the ``MANITHY_DEBUG`` environment variable.

    * If the variable is set to ``"true"`` (case-insensitive) →
      return ``True``.
    * Any other value (or absence) → return ``False``.

    Returns
    -------
    bool
        ``True`` if debug logging should be active, ``False`` otherwise.
    """
    raw = os.environ.get("MANITHY_DEBUG", "false")
    return raw.strip().lower() == "true"
