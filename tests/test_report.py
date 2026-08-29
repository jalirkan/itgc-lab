import copy
import os
import tempfile
import unittest

from core.stats import HIGHER_IS_BETTER, Measurement
from report.document import (
    bullets, doc, kv, note, p, render_html, render_markdown, section, table,
    write_document,
)
from report.guard import (
    GuardError, check_language, check_offline, check_rates,
)


def tiny_doc(*blocks):
    return doc("Test document", "subtitle", section("Section", *blocks))


class LanguageGuard(unittest.TestCase):
    def test_incident_and_conclusory_terms_fire(self):
        for bad in ("a breach occurred", "the account was compromised",
                    "clear fraud", "this violation proves",
                    "the attacker moved", "a security incident",
                    "user is noncompliant", "the control failed"):
            with self.assertRaises(GuardError, msg=bad):
                check_language("Routine sentence. " + bad + ". More text.")

    def test_planted_class_identifiers_are_allowed(self):
        check_language("Class change.freeze_violation was planted 7 times.")
        check_language("access.terminated_active recall shown above.")

    def test_ordinary_audit_language_passes(self):
        check_language("Two exceptions were noted; both are leads for "
                       "follow-up. The account remains active.")

    def test_rate_guard(self):
        with self.assertRaises(GuardError):
            check_rates("Dormancy affected 12% of the population.")
        m = Measurement.proportion("recall", 5, 7,
                                   direction=HIGHER_IS_BETTER)
        check_rates(m.render())
        check_rates("Flags: 12 of 341 records.")

    def test_offline_guard(self):
        for bad in ("<script>x()</script>", "<link rel=x>",
                    "see http://example.test", "https://example.test"):
            with self.assertRaises(GuardError):
                check_offline("<html>" + bad + "</html>")


class RendererGuardsAtTheBoundary(unittest.TestCase):
    """The renderer refuses, not a convention (lab D-024): both formats,
    prose and table cells."""

    def test_bad_paragraph_refused_in_both_formats(self):
        bad = tiny_doc(p("The population was compromised."))
        with self.assertRaises(GuardError):
            render_markdown(bad)
        with self.assertRaises(GuardError):
            render_html(bad)

    def test_bad_table_cell_refused_in_both_formats(self):
        bad = tiny_doc(table(["h"], [["contains a breach signal"]]))
        with self.assertRaises(GuardError):
            render_markdown(bad)
        with self.assertRaises(GuardError):
            render_html(bad)

    def test_bare_rate_refused(self):
        bad = tiny_doc(p("Roughly 73% looked fine."))
        with self.assertRaises(GuardError):
            render_markdown(bad)

    def test_clean_document_renders_in_both_formats(self):
        m = Measurement.proportion("recall", 6, 7,
                                   direction=HIGHER_IS_BETTER)
        good = tiny_doc(p("Two leads were raised."),
                        kv([("Recall", m.render())]),
                        table(["a", "b"], [["1", "2 of 4"]]),
                        bullets(["item one"]), note("A note."))
        md = render_markdown(good)
        html = render_html(good)
        self.assertIn("Two leads were raised.", md)
        self.assertIn("n=7", md)
        self.assertIn("Two leads were raised.", html)

    def test_html_is_self_contained_and_escaped(self):
        d = tiny_doc(p("Text with <b>markup</b> & ampersand."))
        html = render_html(d)
        self.assertIn("&lt;b&gt;markup&lt;/b&gt;", html)
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)
        self.assertNotIn("<script", html)
        self.assertNotIn("<link", html)
        self.assertIn("<style>", html)


class WorkpaperPack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from access.engine import run_access_review
        from baseline.engine import run_baseline_review
        from change.engine import run_change_review
        from enterprise.violations import CLASSES, inject
        from tests.helpers import default_enterprise
        cls.ent = default_enterprise()
        cls.planted, cls.manifest = inject(
            cls.ent, {c: 2 for c in CLASSES}, "wp-001")
        cls.access = run_access_review(cls.planted)
        cls.change = run_change_review(cls.planted)
        cls.config = run_baseline_review(cls.planted)

    def test_every_rule_workpaper_renders_clean(self):
        from report.workpapers import rule_workpaper
        for res in self.access + self.change + self.config:
            d = rule_workpaper(res, self.planted)
            md = render_markdown(d)
            html = render_html(d)
            self.assertIn(res.rule_id, md)
            self.assertIn("RELEVANT", md)
            self.assertIn("CISA D", md)
            self.assertIn(res.criterion, md.replace("\n", " ") + md)
            self.assertTrue(html.startswith("<!DOCTYPE html>"))

    def test_lead_sheet_separates_sections(self):
        from report.workpapers import lead_sheet
        md = render_markdown(lead_sheet(self.access, self.change,
                                        self.config, self.planted))
        self.assertIn("## Exceptions raised for follow-up", md)
        # The baseline engine's leads reach the pack, not just the card.
        self.assertIn("CFG-PWD", md)
        self.assertIn("CFG-ENRL", md)
        self.assertIn("## Review leads (recordkeeping)", md)
        self.assertNotIn("## Procedures unable to conclude", md)

    def test_lead_sheet_lists_scope_limitations_separately(self):
        from access.engine import run_access_review
        from baseline.engine import run_baseline_review
        from change.engine import run_change_review
        from report.workpapers import lead_sheet
        crippled = copy.deepcopy(self.ent)
        crippled["policy"]["thresholds"] = {}
        del crippled["policy"]["config_standard"]
        md = render_markdown(lead_sheet(run_access_review(crippled),
                                        run_change_review(crippled),
                                        run_baseline_review(crippled),
                                        crippled))
        self.assertIn("## Procedures unable to conclude", md)
        self.assertIn("refusing rather than assuming", md)
        # A baseline with no stated standard is a scope limitation, not a
        # clean run: every CFG rule appears in that section.
        for rule_id in ("CFG-PWD", "CFG-HARD", "CFG-MFA", "CFG-ENRL"):
            self.assertIn(rule_id, md)

    def test_card_and_coverage_docs_render(self):
        from frameworks.catalog import coverage
        from report.workpapers import card_doc, coverage_doc
        from reportcard.card import build_report_card
        card = build_report_card(
            base_seed="wp-card", n_seeds=1,
            plan={"access.orphan_account": 1, "change.stale_ticket": 1})
        md = render_markdown(card_doc(card))
        self.assertIn("Wilson", md)
        self.assertIn("no composite score", md.lower())
        self.assertIn("Baseline rules", md)
        self.assertIn("baseline engine", md)
        every = self.access + self.change + self.config
        cov_md = render_markdown(coverage_doc(coverage(every)))
        self.assertIn("tested-with-exceptions", cov_md)
        render_html(card_doc(card))
        render_html(coverage_doc(coverage(every)))

    def test_write_document_emits_both_files(self):
        from report.workpapers import rule_workpaper
        d = rule_workpaper(self.access[0], self.planted)
        with tempfile.TemporaryDirectory() as tmp:
            base = os.path.join(tmp, "wp-acc-term")
            md_path, html_path = write_document(d, base)
            self.assertTrue(os.path.exists(md_path))
            self.assertTrue(os.path.exists(html_path))
            with open(html_path, "rb") as fh:
                self.assertNotIn(b"\r", fh.read())


if __name__ == "__main__":
    unittest.main()
