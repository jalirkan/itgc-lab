import copy
import unittest

from access.rules import ACCESS_RULES
from change.rules import CHANGE_RULES
from frameworks.catalog import (
    MAX_SUMMARY_CHARS, CatalogError, control_summary, controls, coverage,
    rule_map, validate_catalogs, validate_map,
)

ALL_RULE_IDS = tuple(r.rule_id for r in ACCESS_RULES + CHANGE_RULES)


class CatalogGuards(unittest.TestCase):
    def test_shipped_catalogs_validate(self):
        self.assertTrue(validate_catalogs())

    def test_length_guard_fires_on_simulated_paste(self):
        data = copy.deepcopy(controls())
        data["catalogs"]["iso-27001-2022"]["controls"]["A.5.18"] = "x" * (
            MAX_SUMMARY_CHARS + 1)
        with self.assertRaises(CatalogError):
            validate_catalogs(data)

    def test_quote_guard_fires_on_simulated_paste(self):
        data = copy.deepcopy(controls())
        data["catalogs"]["cobit-2019"]["controls"]["DSS05.04"] = (
            'The framework states "' + "framework text " * 6 + '" verbatim.')
        with self.assertRaises(CatalogError):
            validate_catalogs(data)

    def test_partiality_note_required(self):
        data = copy.deepcopy(controls())
        del data["verified"]["partiality"]
        with self.assertRaises(CatalogError):
            validate_catalogs(data)


class MapGuards(unittest.TestCase):
    def test_shipped_map_validates_and_covers_every_rule(self):
        self.assertTrue(validate_map(known_rule_ids=ALL_RULE_IDS))

    def test_every_mapping_resolves(self):
        for entry in rule_map()["rules"].values():
            for ref in entry["controls"]:
                self.assertTrue(control_summary(ref["id"]))

    def test_rationale_is_mandatory(self):
        data = copy.deepcopy(rule_map())
        data["rules"]["ACC-TERM"]["controls"][0]["rationale"] = "  "
        with self.assertRaises(CatalogError):
            validate_map(data)

    def test_unknown_control_rejected(self):
        data = copy.deepcopy(rule_map())
        data["rules"]["ACC-TERM"]["controls"][0]["id"] = "iso-27001-2022:A.99.9"
        with self.assertRaises(CatalogError):
            validate_map(data)

    def test_unmapped_rule_rejected(self):
        data = copy.deepcopy(rule_map())
        del data["rules"]["CHG-FRZ"]
        with self.assertRaises(CatalogError):
            validate_map(data, known_rule_ids=ALL_RULE_IDS)

    def test_cisa_tags_follow_the_outline(self):
        """Access rules tag Domain 5; change rules tag Domain 4 (with 3B
        allowed for release scheduling) — honest to the ISACA outline
        rather than to this project's Domain 5 framing (D-016)."""
        for rule_id, entry in rule_map()["rules"].items():
            domains = {t["domain"] for t in entry["cisa"]}
            if rule_id.startswith("ACC-"):
                self.assertEqual(domains, {5}, rule_id)
            else:
                self.assertIn(4, domains, rule_id)
                self.assertTrue(domains <= {3, 4}, rule_id)


class CoverageReport(unittest.TestCase):
    def test_clean_run_covers_everything_without_exceptions(self):
        from access.engine import run_access_review
        from change.engine import run_change_review
        from tests.helpers import default_enterprise
        results = (run_access_review(default_enterprise())
                   + run_change_review(default_enterprise()))
        cov = coverage(results)
        self.assertEqual(cov["catalog_controls_with_no_mapped_rule"], [])
        for entry in cov["controls"]:
            self.assertEqual(entry["status"], "tested-no-exceptions-noted",
                             entry["control"])
        self.assertIn("not a statement", cov["partiality_note"])

    def test_planted_run_shows_tested_with_exceptions(self):
        from access.engine import run_access_review
        from change.engine import run_change_review
        from enterprise.violations import CLASSES, inject
        from tests.helpers import default_enterprise
        planted, _ = inject(default_enterprise(),
                            {c: 2 for c in CLASSES}, "cov-001")
        results = run_access_review(planted) + run_change_review(planted)
        cov = coverage(results)
        by_control = {e["control"]: e for e in cov["controls"]}
        self.assertEqual(by_control["iso-27001-2022:A.5.3"]["status"],
                         "tested-with-exceptions")
        self.assertEqual(by_control["cobit-2019:BAI06.02"]["status"],
                         "tested-with-exceptions")

    def test_refused_rules_render_inconclusive_coverage(self):
        from access.engine import run_access_review
        from change.engine import run_change_review
        from tests.helpers import default_enterprise
        ent = copy.deepcopy(default_enterprise())
        ent["policy"]["thresholds"] = {}
        results = run_access_review(ent) + run_change_review(ent)
        cov = coverage(results)
        by_control = {e["control"]: e for e in cov["controls"]}
        # A.8.2 is evidenced only by ACC-DORM, which refused.
        self.assertEqual(by_control["iso-27001-2022:A.8.2"]["status"],
                         "inconclusive")


if __name__ == "__main__":
    unittest.main()
