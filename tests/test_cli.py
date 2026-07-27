import contextlib
import io
import json
import os
import tempfile
import unittest

import cli
from core.canonical import canonical_bytes


def run_cli(*argv):
    with contextlib.redirect_stdout(io.StringIO()):
        return cli.main(list(argv))


class CliRoundTrip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.ent_dir = os.path.join(cls.tmp.name, "ent")
        cls.review_dir = os.path.join(cls.tmp.name, "review")
        rc = run_cli("generate", "--seed", "cli-t1", "--out", cls.ent_dir,
                     "--plant-all", "1")
        assert rc == 0

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_generate_wrote_enterprise_and_manifest(self):
        for name in ("roster", "iam", "tickets", "deploys", "exceptions",
                     "policy", "manifest"):
            self.assertTrue(
                os.path.exists(os.path.join(self.ent_dir, name + ".json")),
                name)
        with open(os.path.join(self.ent_dir, "manifest.json"),
                  encoding="ascii") as fh:
            manifest = json.load(fh)
        self.assertEqual(len(manifest["violations"]), 13)

    def test_generate_is_deterministic_at_the_file_level(self):
        other = os.path.join(self.tmp.name, "ent2")
        run_cli("generate", "--seed", "cli-t1", "--out", other,
                "--plant-all", "1")
        for name in ("iam", "manifest", "policy"):
            with open(os.path.join(self.ent_dir, name + ".json"), "rb") as fh:
                a = fh.read()
            with open(os.path.join(other, name + ".json"), "rb") as fh:
                b = fh.read()
            self.assertEqual(a, b, name)

    def test_review_emits_findings_and_documents(self):
        rc = run_cli("review", "--dir", self.ent_dir,
                     "--out", self.review_dir)
        self.assertEqual(rc, 0)
        with open(os.path.join(self.review_dir, "findings.json"),
                  encoding="ascii") as fh:
            findings = json.load(fh)
        self.assertEqual(len(findings["access"]), 7)
        self.assertEqual(len(findings["change"]), 6)
        for base in ("leadsheet", "coverage"):
            for ext in (".md", ".html"):
                self.assertTrue(os.path.exists(
                    os.path.join(self.review_dir, base + ext)))
        wp = os.listdir(os.path.join(self.review_dir, "workpapers"))
        self.assertEqual(len(wp), 26)  # 13 rules x 2 formats

    def test_reportcard_command(self):
        out = os.path.join(self.tmp.name, "card")
        rc = run_cli("reportcard", "--base-seed", "cli-rc", "--seeds", "1",
                     "--per-class", "1", "--out", out)
        self.assertEqual(rc, 0)
        with open(os.path.join(out, "card.json"), encoding="ascii") as fh:
            card = json.load(fh)
        self.assertEqual(card["identity"]["n_seeds"], 1)
        self.assertTrue(os.path.exists(os.path.join(out, "card.md")))

    def test_continuous_command(self):
        out = os.path.join(self.tmp.name, "cont")
        rc = run_cli("continuous", "--dir", self.ent_dir,
                     "--prior-days", "120", "--out", out)
        self.assertEqual(rc, 0)
        with open(os.path.join(out, "continuous.json"),
                  encoding="ascii") as fh:
            cont = json.load(fh)
        self.assertEqual(cont["comparison"]["window"]["days"], 120)
        self.assertIn("aging", cont)
        self.assertTrue(os.path.exists(os.path.join(out, "continuous.md")))


class CommittedExampleRegenerates(unittest.TestCase):
    """The committed manifest and the code that regenerates it must not
    diverge silently (per lab D-026, toolkit D-034)."""

    def test_manifest_regenerates_byte_identically(self):
        from enterprise import generator
        from enterprise.config import GenConfig
        from enterprise.violations import inject
        committed_path = os.path.join("examples", "run-001", "manifest.json")
        if not os.path.exists(committed_path):
            self.skipTest("example not built in this checkout")
        with open(committed_path, "rb") as fh:
            committed = fh.read()
        cfg = GenConfig(seed=cli.EXAMPLE_SEED, **cli.EXAMPLE_CONFIG)
        ent = generator.generate(cfg)
        _, manifest = inject(ent, cli.EXAMPLE_PLAN, cli.EXAMPLE_SEED)
        self.assertEqual(canonical_bytes(manifest) + b"\n", committed)

    def test_run_readme_numbers_match_artifacts(self):
        root = os.path.join("examples", "run-001")
        readme_path = os.path.join(root, "README.md")
        if not os.path.exists(readme_path):
            self.skipTest("example not built in this checkout")
        with open(readme_path, encoding="utf-8") as fh:
            readme = fh.read()
        with open(os.path.join(root, "manifest.json"),
                  encoding="ascii") as fh:
            manifest = json.load(fh)
        with open(os.path.join(root, "card.json"), encoding="ascii") as fh:
            card = json.load(fh)
        self.assertIn("{0} planted conditions".format(
            len(manifest["violations"])), readme)
        self.assertIn(card["precision"]["rendered"], readme)
        self.assertIn("**{0}**".format(card["overall_outcome"]), readme)


if __name__ == "__main__":
    unittest.main()
