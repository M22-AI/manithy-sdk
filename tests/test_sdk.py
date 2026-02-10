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
        """capture() must return a dict with status CAPTURED."""
        buf = InMemoryBuffer()
        sdk = ManithySDK(buffer=buf)
        result = sdk.capture(
            context={"actor": "user-1"},
            snapshot={"amount": 50},
        )
        assert result["status"] == "CAPTURED"
        assert "id" in result
        assert len(result["id"]) == 64

    def test_emits_to_buffer(self) -> None:
        """capture() must call buffer.emit() exactly once."""
        buf = InMemoryBuffer()
        sdk = ManithySDK(buffer=buf)
        sdk.capture(context={"actor": "u1"}, snapshot={"k": 1})
        assert len(buf.envelopes) == 1

    def test_deterministic_commit_id(self) -> None:
        """Same snapshot must yield the same commit-ID across calls."""
        buf = InMemoryBuffer()
        sdk = ManithySDK(buffer=buf)
        r1 = sdk.capture(context={"actor": "u1"}, snapshot={"v": 1})
        r2 = sdk.capture(context={"actor": "u1"}, snapshot={"v": 1})
        assert r1["id"] == r2["id"]


# ── Kill-Switch Tests ────────────────────────────────────────────────

class TestKillSwitch:
    """Tests for the ``MANITHY_ENABLED`` environment variable."""

    def test_disabled_returns_skipped(self) -> None:
        """When MANITHY_ENABLED=false, capture() must return SKIPPED."""
        with mock.patch.dict(os.environ, {"MANITHY_ENABLED": "false"}):
            buf = InMemoryBuffer()
            sdk = ManithySDK(buffer=buf)
            result = sdk.capture(
                context={"actor": "u1"}, snapshot={"k": 1}
            )
            assert result["status"] == "SKIPPED"
            assert len(buf.envelopes) == 0

    def test_enabled_by_default(self) -> None:
        """When MANITHY_ENABLED is absent, capture() must proceed."""
        env = os.environ.copy()
        env.pop("MANITHY_ENABLED", None)
        with mock.patch.dict(os.environ, env, clear=True):
            buf = InMemoryBuffer()
            sdk = ManithySDK(buffer=buf)
            result = sdk.capture(
                context={"actor": "u1"}, snapshot={"k": 1}
            )
            assert result["status"] == "CAPTURED"


# ── Fail-Closed Tests ───────────────────────────────────────────────

class TestFailClosed:
    """Verify the SDK never crashes the host application."""

    def test_bad_snapshot_does_not_raise(self) -> None:
        """Passing un-serializable data must return ERROR, not raise."""
        buf = InMemoryBuffer()
        sdk = ManithySDK(buffer=buf)
        result = sdk.capture(
            context={"actor": "u1"}, snapshot={"obj": object()}
        )
        assert result["status"] == "ERROR"
        assert result["error"] == "Internal SDK Error"

    def test_circular_reference_does_not_raise(self) -> None:
        """Passing a circular reference must return ERROR, not raise."""
        buf = InMemoryBuffer()
        sdk = ManithySDK(buffer=buf)
        circular: dict = {"a": 1}
        circular["self"] = circular
        result = sdk.capture(context={"actor": "u1"}, snapshot=circular)
        assert result["status"] == "ERROR"
        assert result["error"] == "Internal SDK Error"

    def test_broken_buffer_does_not_raise(self) -> None:
        """If buffer.emit() throws, capture() must still return ERROR."""

        class BrokenBuffer(CaptureBuffer):
            def emit(self, envelope: dict[str, Any]) -> None:
                raise RuntimeError("boom")

        sdk = ManithySDK(buffer=BrokenBuffer())
        result = sdk.capture(
            context={"actor": "u1"}, snapshot={"k": 1}
        )
        assert result["status"] == "ERROR"
        assert result["error"] == "Internal SDK Error"
