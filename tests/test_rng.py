import unittest

from core.rng import stream


class StreamRNG(unittest.TestCase):
    def test_pinned_first_draws(self):
        """String seeding goes through SHA-512 (CPython seed version 2), so
        these values are stable across platforms and Python versions. If
        this fails, determinism claims must be re-examined (D-006)."""
        r = stream(42, "roster")
        draws = [round(r.random(), 12) for _ in range(3)]
        self.assertEqual(
            draws, [0.271802298361, 0.571647122402, 0.852194226189])
        self.assertEqual(round(stream(42, "iam").random(), 12), 0.619113589082)

    def test_streams_are_isolated(self):
        a1 = stream("s", "a")
        seq1 = [a1.random() for _ in range(5)]
        # Drawing heavily from another stream must not affect this one.
        b = stream("s", "b")
        for _ in range(1000):
            b.random()
        a2 = stream("s", "a")
        seq2 = [a2.random() for _ in range(5)]
        self.assertEqual(seq1, seq2)

    def test_distinct_streams_differ(self):
        self.assertNotEqual(stream("s", "a").random(), stream("s", "b").random())
        self.assertNotEqual(stream("s1", "a").random(), stream("s2", "a").random())


if __name__ == "__main__":
    unittest.main()
