"""Canonical JSON: one logical value, one byte sequence.

Re-implements the pinned-encoding discipline of toolkit D-009 / lab D-007
(see this repo's DECISIONS.md D-006): sorted keys, tight separators,
ASCII-only escapes, NaN/Infinity rejected at encode time. Every hash and
every written export goes through these functions, so "same seed, same
bytes" is a claim about exactly one encoding.
"""

import hashlib
import json

SCHEMA_VERSION = 1


def canonical_dumps(obj) -> str:
    """Encode obj as canonical JSON text (no trailing newline)."""
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def canonical_bytes(obj) -> bytes:
    """Canonical encoding as ASCII bytes."""
    return canonical_dumps(obj).encode("ascii")


def content_hash(obj, length: int = 10) -> str:
    """Short stable hex digest of an object's canonical encoding."""
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()[:length]


def write_canonical(path, obj) -> None:
    """Write canonical JSON + single trailing LF, byte-stable across platforms."""
    with open(path, "w", encoding="ascii", newline="\n") as fh:
        fh.write(canonical_dumps(obj))
        fh.write("\n")


def read_canonical(path):
    with open(path, "r", encoding="ascii") as fh:
        return json.load(fh)
