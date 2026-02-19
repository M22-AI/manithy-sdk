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

def _capture_kwargs() -> dict[str, Any]:
    """Sensible defaults for a valid J01 capture call."""
    return {
        "boundary_kind": "REFUND_COMMIT_T_MINUS_1",
        "boundary_seq": 1,
        "same_thread": True,
        "observed": {
            "action_kind": "REFUND",
            "amount_minor": 12900,
            "currency": "EUR",
        },
        "availability": {
            "psp_refund_capability_known": True,
            "original_payment_state_known": True,
            "chargeback_state_known": False,
        },
        "reentrancy_guard": "SINGLE_CAPTURE_ENFORCED",
    }


class TestCapture:
    """Tests for ``ManithySDK.capture``."""

    def test_returns_captured(self) -> None:
        """capture() must return a dict with status CAPTURED."""
        buf = InMemoryBuffer()
        sdk = ManithySDK(buffer=buf)
        result = sdk.capture(**_capture_kwargs())
        assert result["status"] == "CAPTURED"
        assert "id" in result
        assert len(result["id"]) == 64

    def test_emits_to_buffer(self) -> None:
        """capture() must call buffer.emit() exactly once."""
        buf = InMemoryBuffer()
        sdk = ManithySDK(buffer=buf)
        sdk.capture(**_capture_kwargs())
        assert len(buf.envelopes) == 1

    def test_emitted_event_is_j01(self) -> None:
        """The emitted event must be a valid J01 CommitBoundaryEvent."""
        buf = InMemoryBuffer()
        sdk = ManithySDK(buffer=buf)
        sdk.capture(**_capture_kwargs())
        event = buf.envelopes[0]
        assert event["schema_id"] == "manithy.commit_boundary_event.v1"
        assert "observed" in event
        assert "availability" in event

    def test_deterministic_commit_id(self) -> None:
        """Same observed must yield the same commit-ID across calls."""
        buf = InMemoryBuffer()
        sdk = ManithySDK(buffer=buf)
        r1 = sdk.capture(**_capture_kwargs())
        r2 = sdk.capture(**_capture_kwargs())
        assert r1["id"] == r2["id"]


# ── Kill-Switch Tests ────────────────────────────────────────────────

class TestKillSwitch:
    """Tests for the ``MANITHY_ENABLED`` environment variable."""

    def test_disabled_returns_skipped(self) -> None:
        """When MANITHY_ENABLED=false, capture() must return SKIPPED."""
        with mock.patch.dict(os.environ, {"MANITHY_ENABLED": "false"}):
            buf = InMemoryBuffer()
            sdk = ManithySDK(buffer=buf)
            result = sdk.capture(**_capture_kwargs())
            assert result["status"] == "SKIPPED"
            assert len(buf.envelopes) == 0

    def test_enabled_by_default(self) -> None:
        """When MANITHY_ENABLED is absent, capture() must proceed."""
        env = os.environ.copy()
        env.pop("MANITHY_ENABLED", None)
        with mock.patch.dict(os.environ, env, clear=True):
            buf = InMemoryBuffer()
            sdk = ManithySDK(buffer=buf)
            result = sdk.capture(**_capture_kwargs())
            assert result["status"] == "CAPTURED"


# ── Fail-Closed Tests ───────────────────────────────────────────────

class TestFailClosed:
    """Verify the SDK never crashes the host application."""

    def test_invalid_observed_does_not_raise(self) -> None:
        """Passing invalid observed data must return ERROR, not raise."""
        buf = InMemoryBuffer()
        sdk = ManithySDK(buffer=buf)
        kwargs = _capture_kwargs()
        kwargs["observed"] = {"obj": object()}
        result = sdk.capture(**kwargs)
        assert result["status"] == "ERROR"
        assert result["error"] == "Internal SDK Error"

    def test_invalid_boundary_kind_type_does_not_raise(self) -> None:
        """Passing non-str boundary_kind must return ERROR, not raise."""
        buf = InMemoryBuffer()
        sdk = ManithySDK(buffer=buf)
        kwargs = _capture_kwargs()
        kwargs["boundary_kind"] = 123  # type: ignore[assignment]
        result = sdk.capture(**kwargs)
        assert result["status"] == "ERROR"
        assert result["error"] == "Internal SDK Error"

    def test_broken_buffer_does_not_raise(self) -> None:
        """If buffer.emit() throws, capture() must still return ERROR."""

        class BrokenBuffer(CaptureBuffer):
            def emit(self, envelope: dict[str, Any]) -> None:
                raise RuntimeError("boom")

        sdk = ManithySDK(buffer=BrokenBuffer())
        result = sdk.capture(**_capture_kwargs())
        assert result["status"] == "ERROR"
        assert result["error"] == "Internal SDK Error"
