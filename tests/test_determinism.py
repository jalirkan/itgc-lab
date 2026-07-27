import os
import tempfile
import unittest

from core.canonical import canonical_bytes
from enterprise import generator
from enterprise.config import GenConfig
from tests.helpers import default_config, default_enterprise


class Determinism(unittest.TestCase):
    """Same seed → byte-identical enterprise (D-006, per lab D-007)."""

    def test_same_seed_byte_identical(self):
        again = generator.generate(default_config())
        for name in generator.ARTIFACTS:
            self.assertEqual(
                canonical_bytes(default_enterprise()[name]),
                canonical_bytes(again[name]),
                "artifact {0} not byte-identical across runs".format(name),
            )

    def test_different_seed_differs(self):
        other = generator.generate(GenConfig(seed="itgc-002"))
        self.assertNotEqual(
            canonical_bytes(default_enterprise()["roster"]),
            canonical_bytes(other["roster"]),
        )

    def test_write_load_round_trip_and_file_bytes(self):
        ent = default_enterprise()
        with tempfile.TemporaryDirectory() as tmp:
            d1 = os.path.join(tmp, "a")
            d2 = os.path.join(tmp, "b")
            generator.write(ent, d1)
            generator.write(generator.generate(default_config()), d2)
            for name in generator.ARTIFACTS:
                p1 = os.path.join(d1, name + ".json")
                p2 = os.path.join(d2, name + ".json")
                with open(p1, "rb") as fh:
                    b1 = fh.read()
                with open(p2, "rb") as fh:
                    b2 = fh.read()
                self.assertEqual(b1, b2, name + " files differ across runs")
                self.assertNotIn(b"\r", b1, name + " must use LF endings")
            loaded = generator.load(d1)
            for name in generator.ARTIFACTS:
                self.assertEqual(
                    canonical_bytes(loaded[name]), canonical_bytes(ent[name]))

    def test_policy_echoes_identity(self):
        pol = default_enterprise()["policy"]
        self.assertEqual(pol["seed"], default_config().seed)
        self.assertEqual(pol["snapshot"], default_config().snapshot)
        self.assertEqual(pol["config"]["employees"], default_config().employees)
        self.assertIn("thresholds", pol)
        self.assertTrue(pol["freeze_windows"])


if __name__ == "__main__":
    unittest.main()
