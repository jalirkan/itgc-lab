import unittest

from core.stats import (
    DEFAULT_MIN_SAMPLE, EXCEPTION, HIGHER_IS_BETTER, INCONCLUSIVE,
    LOWER_IS_BETTER, PASS, Measurement, StatsError, decide, wilson_interval,
    z_value,
)


class WilsonIntervals(unittest.TestCase):
    def test_z_pinned(self):
        self.assertAlmostEqual(z_value(0.95), 1.9599639845400536, places=12)

    def test_known_values(self):
        cases = {
            (0, 22): (0.0, 0.148655),
            (1, 8): (0.022417, 0.470888),
            (5, 5): (0.565518, 1.0),
            (3, 40): (0.025836, 0.198642),
            (1, 1000): (0.000177, 0.005643),
            (100, 1000): (0.082909, 0.120152),
        }
        for (k, n), (lo, hi) in cases.items():
            got = wilson_interval(k, n)
            self.assertAlmostEqual(got[0], lo, places=6, msg=(k, n))
            self.assertAlmostEqual(got[1], hi, places=6, msg=(k, n))

    def test_boundaries_pinned_exactly(self):
        self.assertEqual(wilson_interval(0, 7)[0], 0.0)
        self.assertEqual(wilson_interval(7, 7)[1], 1.0)
        self.assertEqual(wilson_interval(0, 0), (0.0, 1.0))

    def test_zero_width_never_happens_for_boundary_counts(self):
        lo, hi = wilson_interval(0, 8)
        self.assertGreater(hi, 0.0)  # the normal approximation would say 0
        lo, hi = wilson_interval(8, 8)
        self.assertLess(lo, 1.0)

    def test_invalid_inputs(self):
        with self.assertRaises(StatsError):
            wilson_interval(5, 3)
        with self.assertRaises(StatsError):
            wilson_interval(-1, 3)
        with self.assertRaises(StatsError):
            z_value(1.5)


class MeasurementConstruction(unittest.TestCase):
    def test_sanctioned_constructor(self):
        m = Measurement.proportion("leak rate", 3, 40,
                                   direction=LOWER_IS_BETTER)
        self.assertTrue(m.is_informative)
        self.assertAlmostEqual(m.value, 0.075)
        self.assertEqual(m.n, 40)

    def test_bare_rate_is_unconstructible(self):
        with self.assertRaises(StatsError):
            Measurement(kind="proportion", label="x", numerator=1, n=8,
                        value=0.125, interval=None, method="wilson",
                        confidence=0.95, direction=LOWER_IS_BETTER)
        with self.assertRaises(StatsError):
            Measurement(kind="proportion", label="x", numerator=1, n=8,
                        value=0.125, interval=(0.0, 0.5), method="normal",
                        confidence=0.95, direction=LOWER_IS_BETTER)
        with self.assertRaises(StatsError):
            Measurement.proportion("x", 1, 8, direction="sideways")

    def test_render_always_includes_n(self):
        m = Measurement.proportion("recall", 5, 5, direction=HIGHER_IS_BETTER)
        text = m.render()
        self.assertIn("n=5", text)
        self.assertIn("Wilson", text)
        empty = Measurement.proportion("recall", 0, 0,
                                       direction=HIGHER_IS_BETTER)
        self.assertFalse(empty.is_informative)
        self.assertIn("not tested", empty.render())
        self.assertIn("n=0", empty.render())
        self.assertNotIn("0.0%\n", empty.render())


class Decisions(unittest.TestCase):
    def m(self, k, n, direction=LOWER_IS_BETTER):
        return Measurement.proportion("rate", k, n, direction=direction)

    def test_three_outcomes_against_the_interval(self):
        self.assertEqual(decide(self.m(1, 1000), 0.05).outcome, PASS)
        self.assertEqual(decide(self.m(100, 1000), 0.05).outcome, EXCEPTION)
        # 1/8 = 12.5%, interval straddles 5%: the sample cannot answer.
        self.assertEqual(decide(self.m(1, 8), 0.05).outcome, INCONCLUSIVE)

    def test_min_sample_gates_only_the_pass(self):
        # Clean-looking but tiny: interval clears, n does not.
        self.assertEqual(decide(self.m(0, 5), 0.5).outcome, INCONCLUSIVE)
        # Bad and tiny: exceptions count regardless of n.
        self.assertEqual(decide(self.m(5, 5), 0.5).outcome, EXCEPTION)

    def test_zero_tolerance_uses_attribute_rule(self):
        self.assertEqual(decide(self.m(0, 22), 0.0).outcome, PASS)
        self.assertEqual(decide(self.m(1, 22), 0.0).outcome, EXCEPTION)
        self.assertEqual(decide(self.m(0, 10), 0.0).outcome, INCONCLUSIVE)
        self.assertGreaterEqual(DEFAULT_MIN_SAMPLE, 20)

    def test_higher_is_better_mirrors(self):
        rec = self.m(48, 50, HIGHER_IS_BETTER)
        self.assertEqual(decide(rec, 0.8).outcome, PASS)
        self.assertEqual(decide(self.m(10, 50, HIGHER_IS_BETTER), 0.8).outcome,
                         EXCEPTION)
        self.assertEqual(decide(self.m(5, 6, HIGHER_IS_BETTER), 0.8).outcome,
                         INCONCLUSIVE)
        # Perfection threshold flips to the attribute rule.
        self.assertEqual(decide(self.m(22, 22, HIGHER_IS_BETTER), 1.0).outcome,
                         PASS)
        self.assertEqual(decide(self.m(21, 22, HIGHER_IS_BETTER), 1.0).outcome,
                         EXCEPTION)
        self.assertEqual(decide(self.m(10, 10, HIGHER_IS_BETTER), 1.0).outcome,
                         INCONCLUSIVE)

    def test_n_zero_is_inconclusive(self):
        self.assertEqual(decide(self.m(0, 0), 0.05).outcome, INCONCLUSIVE)

    def test_reasons_present(self):
        for k, n, thr in [(0, 22, 0.0), (1, 22, 0.0), (1, 8, 0.05)]:
            d = decide(self.m(k, n), thr)
            self.assertTrue(d.reason)


if __name__ == "__main__":
    unittest.main()
