import os
import tempfile
import unittest

from core.canonical import (
    canonical_bytes, canonical_dumps, content_hash, read_canonical,
    write_canonical,
)


class CanonicalKnownVectors(unittest.TestCase):
    """The encoding is pinned; if these fail, every byte-identity claim in
    the repo changes meaning (DECISIONS.md D-006)."""

    def test_known_vector(self):
        self.assertEqual(
            canonical_dumps({"b": 1, "a": [1.5, "é"]}),
            '{"a":[1.5,"\\u00e9"],"b":1}',
        )

    def test_known_hash(self):
        self.assertEqual(content_hash(["known", "vector", 7]), "9878e828b4")

    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            canonical_dumps({"x": float("nan")})
        with self.assertRaises(ValueError):
            canonical_dumps(float("inf"))

    def test_key_order_irrelevant(self):
        self.assertEqual(
            canonical_bytes({"a": 1, "b": 2}),
            canonical_bytes({"b": 2, "a": 1}),
        )


class CanonicalFiles(unittest.TestCase):
    def test_write_is_lf_and_round_trips(self):
        obj = {"z": [1, 2], "a": "text"}
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "x.json")
            write_canonical(path, obj)
            with open(path, "rb") as fh:
                raw = fh.read()
            self.assertTrue(raw.endswith(b"\n"))
            self.assertNotIn(b"\r", raw)
            self.assertEqual(raw, canonical_bytes(obj) + b"\n")
            self.assertEqual(read_canonical(path), obj)


if __name__ == "__main__":
    unittest.main()
