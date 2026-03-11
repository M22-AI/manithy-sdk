"""
tests.test_core
~~~~~~~~~~~~~~~

Unit tests for the deterministic core modules:
    - manithy.core.canonical  (to_canonical_bytes)
    - manithy.core.hasher     (generate_commit_id)
    - manithy.core.envelope   (build_envelope)

Owner: [Dev A] — must populate ``vectors.json`` with Golden Vectors
and write tests that exercise cross-language determinism guarantees.

Test Strategy
-------------
* Load golden vectors from ``tests/vectors.json``.
* For each vector, assert that ``to_canonical_bytes(input)`` produces
  the expected byte string.
* Assert that ``generate_commit_id(input)`` returns the expected
  SHA-256 hex digest.
* Assert that ``build_envelope(...)`` returns a dict with the correct
  schema (spec, id, meta, data).
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import pytest

from manithy.core.canonical import to_canonical_bytes
from manithy.core.envelope import (
    SCHEMA_ID,
    SCHEMA_ID_V1,
    SCHEMA_ID_V2,
    build_commit_boundary_event,
)
from manithy.core.hasher import generate_commit_id

VECTORS_PATH = pathlib.Path(__file__).parent / "vectors.json"


@pytest.fixture
def golden_vectors() -> list[dict]:
    """Load golden test vectors from vectors.json.

    Each vector should be a dict with at least:
        {
            "input": { ... },
            "expected_canonical": "<canonical json string>",
            "expected_commit_id": "<sha256 hex>"
        }

    TODO: [Dev A] populate vectors.json with real golden vectors
    that have been validated against the Node.js reference
    implementation.
    """
    with VECTORS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


# ── Canonical Tests ──────────────────────────────────────────────────

class TestCanonical:
    """Tests for ``to_canonical_bytes``."""

    def test_sorts_keys(self) -> None:
        """Verify that dictionary keys are sorted lexicographically."""
        result = to_canonical_bytes({"b": 1, "a": 2})
        assert result == b'{"a":2,"b":1}'

    def test_float_to_int_coercion(self) -> None:
        """Verify that 100.0 becomes 100 in the output."""
        result = to_canonical_bytes({"v": 100.0})
        assert result == b'{"v":100}'

    def test_nested_sort_and_coercion(self) -> None:
        """Verify recursion into nested dicts and lists."""
        data = {"b": 1, "a": [3.0, {"d": 4, "c": 5}]}
        result = to_canonical_bytes(data)
        assert result == b'{"a":[3,{"c":5,"d":4}],"b":1}'

    def test_golden_vectors(self, golden_vectors: list[dict]) -> None:
        """Validate canonical output against golden vectors."""
        if not golden_vectors:
            pytest.skip("No golden vectors defined yet")
        for vec in golden_vectors:
            result = to_canonical_bytes(vec["input"])
            assert result == vec["expected_canonical"].encode("utf-8"), (
                f"Vector '{vec.get('name', '?')}' canonical mismatch"
            )


# ── Hasher Tests ─────────────────────────────────────────────────────

class TestHasher:
    """Tests for ``generate_commit_id``."""

    def test_determinism(self) -> None:
        """Same input must always produce the same commit-ID."""
        data = {"x": 42}
        assert generate_commit_id(data) == generate_commit_id(data)

    def test_hex_format(self) -> None:
        """Commit-ID must be a 64-char lowercase hex string."""
        result = generate_commit_id({"key": "value"})
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_golden_vectors(self, golden_vectors: list[dict]) -> None:
        """Validate commit-ID against golden vectors."""
        if not golden_vectors:
            pytest.skip("No golden vectors defined yet")
        for vec in golden_vectors:
            result = generate_commit_id(vec["input"])
            assert result == vec["expected_hash"], (
                f"Vector '{vec.get('name', '?')}' hash mismatch"
            )


# ── J01 CommitBoundaryEvent Tests ────────────────────────────────────


def _make_event(**overrides: Any) -> dict[str, Any]:
    """Helper: build a valid J01 event with sensible defaults."""
    defaults: dict[str, Any] = {
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
    defaults.update(overrides)
    return build_commit_boundary_event(**defaults)


class TestCommitBoundaryEvent:
    """Tests for ``build_commit_boundary_event`` (J01)."""

    def test_schema_keys(self) -> None:
        """Event must contain exactly the J01 top-level keys."""
        event = _make_event()
        assert set(event.keys()) == {
            "kind",
            "schema_id",
            "commit_seq",
            "meta",
            "boundary",
            "adapter_snapshot",
        }

    def test_schema_id(self) -> None:
        """``schema_id`` must be the pinned v2 identifier."""
        event = _make_event()
        assert event["schema_id"] == SCHEMA_ID

    def test_boundary_kind_accepts_str(self) -> None:
        """``boundary_kind`` accepts any non-empty string (consumer-defined)."""
        event = _make_event(boundary_kind="REFUND_COMMIT_T_MINUS_1")
        assert event["boundary"]["boundary_kind"] == "REFUND_COMMIT_T_MINUS_1"
        event2 = _make_event(boundary_kind="CUSTOM_DOMAIN_KIND")
        assert event2["boundary"]["boundary_kind"] == "CUSTOM_DOMAIN_KIND"

    def test_empty_boundary_kind_rejected(self) -> None:
        """Empty string boundary_kind must raise TypeError."""
        with pytest.raises(TypeError):
            _make_event(boundary_kind="")

    def test_non_str_boundary_kind_rejected(self) -> None:
        """Non-string boundary_kind must raise TypeError."""
        with pytest.raises(TypeError):
            _make_event(boundary_kind=123)

    def test_boundary_seq_range(self) -> None:
        """boundary_seq must be a small non-negative integer."""
        event = _make_event(boundary_seq=0)
        assert event["boundary"]["boundary_seq"] == 0
        with pytest.raises(ValueError):
            _make_event(boundary_seq=-1)
        with pytest.raises(ValueError):
            _make_event(boundary_seq=256)

    def test_boundary_seq_type(self) -> None:
        """boundary_seq must be int, not bool or float."""
        with pytest.raises(TypeError):
            _make_event(boundary_seq=True)

    def test_same_thread_must_be_bool(self) -> None:
        """same_thread must be bool."""
        with pytest.raises(TypeError):
            _make_event(same_thread=1)

    def test_reentrancy_guard_passthrough(self) -> None:
        """reentrancy_guard value is passed through as-is."""
        event = _make_event()
        assert event["boundary"]["reentrancy_guard"] == "SINGLE_CAPTURE_ENFORCED"

    def test_observed_primitives_only(self) -> None:
        """observed values must be str | int | bool — no floats."""
        with pytest.raises(TypeError):
            _make_event(observed={"amount": 12.5})

    def test_observed_no_none(self) -> None:
        """observed values must not be None."""
        with pytest.raises(TypeError):
            _make_event(observed={"field": None})

    def test_observed_no_nested_dicts(self) -> None:
        """observed must not contain nested structures."""
        with pytest.raises(TypeError):
            _make_event(observed={"nested": {"a": 1}})

    def test_availability_must_be_bool(self) -> None:
        """All availability values must be bool."""
        with pytest.raises(TypeError):
            _make_event(availability={"some_known": 1})

    def test_unknown_fact_must_not_appear_in_observed(self) -> None:
        """If availability X_known=False, observed must not have X."""
        with pytest.raises(ValueError, match="unknown facts"):
            _make_event(
                observed={"chargeback_state": "NONE"},
                availability={"chargeback_state_known": False},
            )

    def test_forbidden_field_in_observed(self) -> None:
        """Forbidden joinable fields must be rejected."""
        with pytest.raises(ValueError, match="forbidden"):
            _make_event(
                observed={"producer_invocation_id": "inv_123"},
            )

    def test_valid_full_event(self) -> None:
        """A complete valid event must match the J01 shape."""
        event = _make_event()
        assert event["schema_id"] == SCHEMA_ID_V2
        assert event["boundary"]["boundary_kind"] == "REFUND_COMMIT_T_MINUS_1"
        assert event["boundary"]["boundary_seq"] == 1
        assert event["boundary"]["same_thread"] is True
        assert event["boundary"]["reentrancy_guard"] == "SINGLE_CAPTURE_ENFORCED"
        assert event["adapter_snapshot"]["observed"]["action_kind"] == "REFUND"
        assert event["adapter_snapshot"]["observed"]["amount_minor"] == 12900
        assert (
            event["adapter_snapshot"]["availability"]["chargeback_state_known"] is False
        )

    def test_v1_compat_shape(self) -> None:
        """Builder should support the legacy v1 envelope shape."""
        event = _make_event(schema_version="v1")
        assert event["schema_id"] == SCHEMA_ID_V1
        assert set(event.keys()) == {
            "schema_id",
            "boundary_kind",
            "boundary_seq",
            "same_thread",
            "reentrancy_guard",
            "observed",
            "availability",
        }

    def test_invalid_schema_version_rejected(self) -> None:
        """Only v1 and v2 are supported schema versions."""
        with pytest.raises(ValueError):
            _make_event(schema_version="v3")
