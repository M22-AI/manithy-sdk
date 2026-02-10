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
    with VECTORS_PATH.open() as f:
        return json.load(f)


# ── Canonical Tests ──────────────────────────────────────────────────

class TestCanonical:
    """Tests for ``to_canonical_bytes``."""

    def test_sorts_keys(self) -> None:
        """Verify that dictionary keys are sorted lexicographically."""
        # TODO: Implement — e.g. {"b":1,"a":2} → b'{"a":2,"b":1}'
        pass

    def test_float_to_int_coercion(self) -> None:
        """Verify that 100.0 becomes 100 in the output."""
        # TODO: Implement — e.g. {"v":100.0} → b'{"v":100}'
        pass

    def test_nested_sort_and_coercion(self) -> None:
        """Verify recursion into nested dicts and lists."""
        # TODO: Implement with a deeply nested structure.
        pass

    def test_golden_vectors(self, golden_vectors: list[dict]) -> None:
        """Validate canonical output against golden vectors."""
        # TODO: Skip if vectors are empty; iterate and assert.
        if not golden_vectors:
            pytest.skip("No golden vectors defined yet")
        for vec in golden_vectors:
            result = to_canonical_bytes(vec["input"])
            assert result == vec["expected_canonical"].encode("utf-8")


# ── Hasher Tests ─────────────────────────────────────────────────────

class TestHasher:
    """Tests for ``generate_commit_id``."""

    def test_determinism(self) -> None:
        """Same input must always produce the same commit-ID."""
        # TODO: Implement — call twice, assert equal.
        pass

    def test_hex_format(self) -> None:
        """Commit-ID must be a 64-char lowercase hex string."""
        # TODO: Implement — assert len==64 and all hex chars.
        pass

    def test_golden_vectors(self, golden_vectors: list[dict]) -> None:
        """Validate commit-ID against golden vectors."""
        if not golden_vectors:
            pytest.skip("No golden vectors defined yet")
        for vec in golden_vectors:
            result = generate_commit_id(vec["input"])
            assert result == vec["expected_commit_id"]


# ── Envelope Tests ───────────────────────────────────────────────────

class TestEnvelope:
    """Tests for ``build_envelope``."""

    def test_schema_keys(self) -> None:
        """Envelope must contain exactly: spec, id, meta, data."""
        # TODO: Implement — build envelope, assert key set.
        pass

    def test_spec_version(self) -> None:
        """``spec`` must always be '1.0'."""
        # TODO: Implement.
        pass

    def test_meta_contains_timestamp(self) -> None:
        """``meta.ts`` must be present and look like ISO-8601."""
        # TODO: Implement.
        pass

    def test_context_merged_into_meta(self) -> None:
        """All context keys must appear in ``meta``."""
        # TODO: Implement.
        pass
