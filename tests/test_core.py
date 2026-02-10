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

import pytest

from manithy.core.canonical import to_canonical_bytes
from manithy.core.envelope import build_envelope
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


# ── Envelope Tests ───────────────────────────────────────────────────

class TestEnvelope:
    """Tests for ``build_envelope``."""

    def test_schema_keys(self) -> None:
        """Envelope must contain exactly: spec, id, meta, data."""
        envelope = build_envelope("abc123", {"actor": "u1"}, {"k": 1})
        assert set(envelope.keys()) == {"spec", "id", "meta", "data"}

    def test_spec_version(self) -> None:
        """``spec`` must always be '1.0'."""
        envelope = build_envelope("abc123", {}, {})
        assert envelope["spec"] == "1.0"

    def test_meta_contains_timestamp(self) -> None:
        """``meta.ts`` must be present and look like ISO-8601."""
        envelope = build_envelope("abc123", {}, {})
        assert "ts" in envelope["meta"]
        assert "T" in envelope["meta"]["ts"]  # ISO-8601 contains 'T'

    def test_context_merged_into_meta(self) -> None:
        """All context keys must appear in ``meta``."""
        ctx = {"actor": "user-1", "action": "approve"}
        envelope = build_envelope("abc123", ctx, {})
        assert envelope["meta"]["actor"] == "user-1"
        assert envelope["meta"]["action"] == "approve"
