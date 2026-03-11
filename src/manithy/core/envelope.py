"""
manithy.core.envelope
~~~~~~~~~~~~~~~~~~~~~

J01 — CommitBoundaryEvent Assembly.

A CommitBoundaryEvent marks the exact t-1 boundary before an
irreversible action and captures **only** facts already resolved in
the execution context — no lookups, no inference, no enrichment.

Owner: [Dev A]

CommitBoundaryEvent Schema (``manithy.commit_boundary_event.v1``)
-----------------------------------------------------------------
::

    {
      "schema_id": "manithy.commit_boundary_event.v1",
      "boundary_kind": "<BoundaryKind enum>",
      "boundary_seq": <small int>,
      "same_thread": <bool>,
      "reentrancy_guard": "<ReentrancyGuard enum>",
      "observed": { ...runtime facts (primitives only)... },
      "availability": { ..._known booleans... }
    }

Forbidden fields (must NEVER appear)
-------------------------------------
* ``producer_invocation_id`` — joinable per-event ID; single-capture
  is enforced via guard state, not IDs.
* ``callsite_id`` — high joinability risk.
* ``producer_build_id`` — belongs in PackInit / EvidencePack provenance.

Blocks
------
* **observed** — runtime facts that were already resolved at t-1.
  Values must be primitives only (``str``, ``int``, ``bool``).
  No floats, no ``None``, no nested structures.

* **availability** — epistemic visibility declaration.
  Each key answers: "Was this fact knowable at t-1?"
  Values must be ``bool``.  ``False`` means UNKNOWN (a first-class
  state, never inferred).  If ``known`` is ``False`` the corresponding
  value must NOT appear in ``observed``.
"""

from __future__ import annotations

from typing import Any

SCHEMA_ID_V1 = "manithy.commit_boundary_event.v1"
SCHEMA_ID_V2 = "manithy.commit_boundary_event.v2"
SCHEMA_ID = SCHEMA_ID_V2

_FORBIDDEN_FIELDS = frozenset({
    "producer_invocation_id",
    "callsite_id",
    "producer_build_id",
})


# ── Validation Helpers ───────────────────────────────────────────────

_OBSERVED_ALLOWED_TYPES = (str, int, bool)

_MAX_BOUNDARY_SEQ = 255


def _validate_boundary_seq(seq: int) -> None:
    """``boundary_seq`` must be a small non-negative integer."""
    if not isinstance(seq, int) or isinstance(seq, bool):
        raise TypeError(
            f"boundary_seq must be int, got {type(seq).__name__}"
        )
    if seq < 0 or seq > _MAX_BOUNDARY_SEQ:
        raise ValueError(
            f"boundary_seq must be 0..{_MAX_BOUNDARY_SEQ}, got {seq}"
        )


def _validate_observed(observed: dict[str, Any]) -> None:
    """All observed values must be already-resolved primitives."""
    for key, value in observed.items():
        if key in _FORBIDDEN_FIELDS:
            raise ValueError(
                f"forbidden field '{key}' in observed block"
            )
        if not isinstance(value, _OBSERVED_ALLOWED_TYPES):
            raise TypeError(
                f"observed['{key}'] must be str | int | bool, "
                f"got {type(value).__name__}"
            )
        # bool is a subclass of int in Python — but floats must be
        # rejected.  The isinstance check above already handles this
        # because float is not in _OBSERVED_ALLOWED_TYPES.


def _validate_availability(
    availability: dict[str, bool],
    observed: dict[str, Any],
) -> None:
    """All availability values must be bool.

    If a key is ``False`` (unknown at t-1), the corresponding fact
    must NOT appear in ``observed``.
    """
    for key, value in availability.items():
        if not isinstance(value, bool):
            raise TypeError(
                f"availability['{key}'] must be bool, "
                f"got {type(value).__name__}"
            )
        # Derive the observed-key from the availability key by
        # stripping the ``_known`` suffix (convention).
        if not value:
            # Fact was NOT knowable at t-1 — make sure it's absent.
            base = key.removesuffix("_known")
            if base in observed:
                raise ValueError(
                    f"availability['{key}'] is False but "
                    f"observed['{base}'] is present — "
                    f"unknown facts must not appear in observed"
                )


# ── Builder ──────────────────────────────────────────────────────────


def build_commit_boundary_event(
    boundary_kind: str,
    boundary_seq: int,
    same_thread: bool,
    observed: dict[str, Any],
    availability: dict[str, bool],
    reentrancy_guard: str,
    tenant_id: str | None = None,
    action_class: str | None = None,
    commit_point_id: str | None = None,
    auth_metadata: dict[str, Any] | None = None,
    schema_version: str = "v2",
) -> dict[str, Any]:
    """Construct a J01 CommitBoundaryEvent dictionary.

    Parameters
    ----------
    boundary_kind : str
        Which irreversible boundary this event refers to.
        The SDK consumer defines the closed enum of valid values;
        the SDK only enforces that this is a non-empty string.
    boundary_seq : int
        Supports rare cases of multiple irreversible calls in one
        execution path.  Small non-negative integer (0..255).
    same_thread : bool
        Runtime assertion that capture happened same-thread at t-1.
    observed : dict[str, Any]
        Runtime facts already resolved in the execution context.
        Values must be ``str``, ``int``, or ``bool`` only.
    availability : dict[str, bool]
        Epistemic visibility at t-1.  Each key declares whether a
        fact was knowable before the irreversible action.
    reentrancy_guard : str
        Capture enforcement mode.  The SDK consumer defines the
        closed enum of valid values.

    Returns
    -------
    dict[str, Any]
        A dictionary conforming to ``manithy.commit_boundary_event.v1``.

    Raises
    ------
    TypeError
        If any value violates its type constraint.
    ValueError
        If a forbidden field is present, ``boundary_seq`` is out of
        range, or an unknown fact leaks into ``observed``.
    """
    if not isinstance(boundary_kind, str) or not boundary_kind:
        raise TypeError(
            f"boundary_kind must be a non-empty str, "
            f"got {type(boundary_kind).__name__}"
        )
    if not isinstance(reentrancy_guard, str) or not reentrancy_guard:
        raise TypeError(
            f"reentrancy_guard must be a non-empty str, "
            f"got {type(reentrancy_guard).__name__}"
        )

    _validate_boundary_seq(boundary_seq)

    if not isinstance(same_thread, bool):
        raise TypeError(
            f"same_thread must be bool, got {type(same_thread).__name__}"
        )

    _validate_observed(observed)
    _validate_availability(availability, observed)

    if schema_version not in {"v1", "v2"}:
        raise ValueError("schema_version must be 'v1' or 'v2'")

    if tenant_id is not None and (
        not isinstance(tenant_id, str) or not tenant_id.strip()
    ):
        raise TypeError("tenant_id must be a non-empty str when provided")

    if action_class is not None and (
        not isinstance(action_class, str) or not action_class.strip()
    ):
        raise TypeError("action_class must be a non-empty str when provided")

    if commit_point_id is not None and (
        not isinstance(commit_point_id, str) or not commit_point_id.strip()
    ):
        raise TypeError("commit_point_id must be a non-empty str when provided")

    if auth_metadata is not None and not isinstance(auth_metadata, dict):
        raise TypeError("auth_metadata must be a dict when provided")

    if schema_version == "v1":
        return {
            "schema_id": SCHEMA_ID_V1,
            "boundary_kind": boundary_kind,
            "boundary_seq": boundary_seq,
            "same_thread": same_thread,
            "reentrancy_guard": reentrancy_guard,
            "observed": dict(observed),
            "availability": dict(availability),
        }

    meta: dict[str, Any] = {
        "tenant_id": tenant_id or "UNKNOWN_TENANT",
        "action_class": action_class or boundary_kind,
        "commit_point_id": commit_point_id or boundary_kind,
    }
    if auth_metadata:
        meta.update(auth_metadata)

    return {
        "kind": "J01.CommitBoundaryEvent",
        "schema_id": SCHEMA_ID_V2,
        "commit_seq": boundary_seq,
        "meta": meta,
        "boundary": {
            "boundary_kind": boundary_kind,
            "boundary_seq": boundary_seq,
            "same_thread": same_thread,
            "reentrancy_guard": reentrancy_guard,
        },
        "adapter_snapshot": {
            "observed": dict(observed),
            "availability": dict(availability),
        },
    }
