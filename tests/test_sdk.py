"""
tests.test_sdk
~~~~~~~~~~~~~~

Integration tests for ``ManithySDK.capture()`` and the kill-switch.

Owner: [Dev B]

Test Strategy
-------------
* Verify the full capture pipeline produces a valid envelope.
* Verify the kill-switch (``MANITHY_ENABLED=false``) suppresses output.
* Verify fail-closed behaviour: injecting faults must not raise.
"""

from __future__ import annotations

import os
from typing import Any
from unittest import mock

import pytest

from manithy.interfaces.buffer import CaptureBuffer
from manithy.sdk import ManithySDK


class InMemoryBuffer(CaptureBuffer):
    """Test double that captures emitted envelopes in a list."""

    def __init__(self) -> None:
        self.envelopes: list[dict[str, Any]] = []

    def emit(self, envelope: dict[str, Any]) -> None:
        self.envelopes.append(envelope)


# ── SDK Capture Tests ────────────────────────────────────────────────

class TestCapture:
    """Tests for ``ManithySDK.capture``."""

    def test_returns_envelope(self) -> None:
        """capture() must return a dict with spec/id/meta/data keys."""
        # TODO: Instantiate SDK with InMemoryBuffer, call capture,
        #       assert return value has the expected keys.
        pass

    def test_emits_to_buffer(self) -> None:
        """capture() must call buffer.emit() exactly once."""
        # TODO: Use InMemoryBuffer, assert len(buf.envelopes) == 1.
        pass

    def test_deterministic_commit_id(self) -> None:
        """Same snapshot must yield the same commit-ID across calls."""
        # TODO: Call capture twice with same snapshot, compare IDs.
        pass


# ── Kill-Switch Tests ────────────────────────────────────────────────

class TestKillSwitch:
    """Tests for the ``MANITHY_ENABLED`` environment variable."""

    def test_disabled_returns_none(self) -> None:
        """When MANITHY_ENABLED=false, capture() must return None."""
        # TODO: Use unittest.mock.patch.dict(os.environ, ...) to set
        #       MANITHY_ENABLED=false, then assert capture() is None.
        pass

    def test_enabled_by_default(self) -> None:
        """When MANITHY_ENABLED is absent, capture() must proceed."""
        # TODO: Ensure env var is absent, assert capture() returns
        #       a valid envelope.
        pass


# ── Fail-Closed Tests ───────────────────────────────────────────────

class TestFailClosed:
    """Verify the SDK never crashes the host application."""

    def test_bad_snapshot_does_not_raise(self) -> None:
        """Passing un-serializable data must return None, not raise."""
        # TODO: Pass an object() as snapshot, assert no exception
        #       and return value is None.
        pass

    def test_broken_buffer_does_not_raise(self) -> None:
        """If buffer.emit() throws, capture() must still return None."""
        # TODO: Create a buffer whose emit() raises RuntimeError,
        #       assert capture() returns None (not the envelope).
        pass
