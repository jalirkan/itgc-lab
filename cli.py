"""itgc-lab command line.

Commands:
  generate    build a synthetic enterprise (optionally with planted
              violations; the manifest is the only ground truth)
  review      run both rule engines over an enterprise directory and
              write findings, workpapers, lead sheet, and coverage
  reportcard  grade the engines against planted truth across seeds
  continuous  compare a derived prior snapshot with the current one
  example     rebuild examples/run-001 stage by stage

Everything is offline and deterministic: no network, no wall clock in
any artifact, same inputs → same bytes.
"""

import argparse
import json
import os
import sys

from access.engine import run_access_review
from change.engine import run_change_review
from continuous.deltas import age_leads, as_of, compare_snapshots
from core.canonical import canonical_dumps, write_canonical
from enterprise import dates, generator
from enterprise.config import GenConfig
from enterprise.violations import CLASSES, inject
from frameworks.catalog import coverage, validate_catalogs, validate_map
from report.document import write_document
from report.workpapers import (card_doc, continuous_doc, coverage_doc,
                               lead_sheet, rule_workpaper)
from reportcard.card import build_report_card

# --- committed example: parameters are code, so the committed artifacts
# --- and their regeneration cannot drift apart (per lab D-026).
EXAMPLE_SEED = "run-001"
EXAMPLE_CONFIG = dict(employees=5000, months=18, tickets_per_month=40,
                      snapshot="2026-06-30")
EXAMPLE_PLAN = {cls: 4 for cls in CLASSES}          # 52 planted conditions
EXAMPLE_CARD = dict(base_seed="itgc-rc", n_seeds=5)  # 7/class → 35 pooled
EXAMPLE_PRIOR_DAYS = 30


def _write_json(path, obj):
    write_canonical(path, obj)
    return path


def _load_enterprise(path):
    return generator.load(path)


def cmd_generate(args):
    cfg = GenConfig(seed=args.seed, employees=args.employees,
                    months=args.months, snapshot=args.snapshot,
                    tickets_per_month=args.tickets_per_month)
    ent = generator.generate(cfg)
    plan = {}
    if args.plant_all:
        plan = {cls: args.plant_all for cls in CLASSES}
    for spec in args.plant or ():
        cls, _, n = spec.partition("=")
        plan[cls] = int(n)
    if plan:
        ent, manifest = inject(ent, plan, args.plant_seed or args.seed)
        generator.write(ent, args.out)
        _write_json(os.path.join(args.out, "manifest.json"), manifest)
        print("generated {0} (+{1} planted conditions) -> {2}".format(
            args.seed, len(manifest["violations"]), args.out))
    else:
        generator.write(ent, args.out)
        print("generated {0} (clean) -> {1}".format(args.seed, args.out))
    print("employees={0} grants={1} tickets={2} deploys={3}".format(
        len(ent["roster"]["employees"]), len(ent["iam"]["grants"]),
        len(ent["tickets"]["tickets"]), len(ent["deploys"]["deploys"])))
    return 0


def _run_review(ent, outdir):
    validate_catalogs()
    access = run_access_review(ent)
    change = run_change_review(ent)
    validate_map(known_rule_ids=[r.rule_id for r in access + change])
    os.makedirs(outdir, exist_ok=True)
    findings = {
        "identity": {"seed": ent["policy"]["seed"],
                     "snapshot": ent["policy"]["snapshot"],
                     "generator_version": ent["policy"]["generator_version"]},
        "access": [r.to_dict() for r in access],
        "change": [r.to_dict() for r in change],
    }
    _write_json(os.path.join(outdir, "findings.json"), findings)
    wp_dir = os.path.join(outdir, "workpapers")
    os.makedirs(wp_dir, exist_ok=True)
    for res in access + change:
        write_document(rule_workpaper(res, ent),
                       os.path.join(wp_dir, res.rule_id))
    write_document(lead_sheet(access, change, ent),
                   os.path.join(outdir, "leadsheet"))
    write_document(coverage_doc(coverage(access + change)),
                   os.path.join(outdir, "coverage"))
    n_leads = sum(len(r.findings) for r in access + change)
    outcomes = [r.outcome for r in access + change]
    print("review: {0} rules, {1} leads, outcomes: {2} pass / {3} "
          "exception / {4} inconclusive -> {5}".format(
              len(outcomes), n_leads, outcomes.count("pass"),
              outcomes.count("exception"), outcomes.count("inconclusive"),
              outdir))
    return access, change


def cmd_review(args):
    ent = _load_enterprise(args.dir)
    _run_review(ent, args.out)
    return 0


def cmd_reportcard(args):
    card = build_report_card(base_seed=args.base_seed, n_seeds=args.seeds,
                             plan={cls: args.per_class for cls in CLASSES},
                             recall_floor=args.floor)
    os.makedirs(args.out, exist_ok=True)
    _write_json(os.path.join(args.out, "card.json"), card)
    write_document(card_doc(card), os.path.join(args.out, "card"))
    print("report card: overall={0} ({1}) -> {2}".format(
        card["overall_outcome"],
        ", ".join("{0} {1}".format(v, k)
                  for k, v in sorted(card["outcome_counts"].items())),
        args.out))
    return 0


def cmd_continuous(args):
    ent = _load_enterprise(args.dir)
    if args.prior_dir:
        prior = _load_enterprise(args.prior_dir)
    else:
        prior_day = dates.add_days(ent["policy"]["snapshot"],
                                   -args.prior_days)
        prior = as_of(ent, prior_day)
    diff = compare_snapshots(prior, ent)
    aging = age_leads(
        run_access_review(prior) + run_change_review(prior),
        run_access_review(ent) + run_change_review(ent),
        diff["window"]["days"])
    os.makedirs(args.out, exist_ok=True)
    _write_json(os.path.join(args.out, "continuous.json"),
                {"comparison": diff, "aging": aging})
    write_document(continuous_doc(diff, aging),
                   os.path.join(args.out, "continuous"))
    print("continuous: {0} -> {1}, {2} new grants, {3} open leads "
          "({4} persisting) -> {5}".format(
              diff["window"]["from"], diff["window"]["to"],
              diff["grants"]["new_n"], aging["counts"]["open"],
              aging["counts"]["persisting"], args.out))
    return 0


# --- the committed example -------------------------------------------------

def _example_generate(root):
    cfg = GenConfig(seed=EXAMPLE_SEED, **EXAMPLE_CONFIG)
    ent = generator.generate(cfg)
    planted, manifest = inject(ent, EXAMPLE_PLAN, EXAMPLE_SEED)
    exports = os.path.join(root, "exports")
    generator.write(planted, exports)
    _write_json(os.path.join(exports, "manifest.json"), manifest)
    _write_json(os.path.join(root, "manifest.json"), manifest)
    print("example generate: {0} employees, {1} grants, {2} planted".format(
        len(planted["roster"]["employees"]), len(planted["iam"]["grants"]),
        len(manifest["violations"])))
    return planted, manifest


def _example_load_or_generate(root):
    exports = os.path.join(root, "exports")
    if os.path.exists(os.path.join(exports, "policy.json")):
        return generator.load(exports)
    planted, _ = _example_generate(root)
    return planted


def _example_review(root):
    planted = _example_load_or_generate(root)
    return _run_review(planted, root)


def _example_card(root):
    card = build_report_card(**EXAMPLE_CARD)
    _write_json(os.path.join(root, "card.json"), card)
    write_document(card_doc(card), os.path.join(root, "card"))
    print("example card: overall={0}".format(card["overall_outcome"]))
    return card


def _example_continuous(root):
    planted = _example_load_or_generate(root)
    prior_day = dates.add_days(planted["policy"]["snapshot"],
                               -EXAMPLE_PRIOR_DAYS)
    prior = as_of(planted, prior_day)
    diff = compare_snapshots(prior, planted)
    aging = age_leads(
        run_access_review(prior) + run_change_review(prior),
        run_access_review(planted) + run_change_review(planted),
        diff["window"]["days"])
    _write_json(os.path.join(root, "continuous.json"),
                {"comparison": diff, "aging": aging})
    write_document(continuous_doc(diff, aging),
                   os.path.join(root, "continuous"))
    print("example continuous: {0} open leads".format(
        aging["counts"]["open"]))
    return diff, aging


def _example_readme(root):
    """Write the run's README from its own artifacts, so committed prose
    and committed numbers cannot diverge (per lab D-034/D-026)."""
    with open(os.path.join(root, "manifest.json"), encoding="ascii") as fh:
        manifest = json.load(fh)
    with open(os.path.join(root, "findings.json"), encoding="ascii") as fh:
        findings = json.load(fh)
    with open(os.path.join(root, "card.json"), encoding="ascii") as fh:
        card = json.load(fh)
    with open(os.path.join(root, "continuous.json"),
              encoding="ascii") as fh:
        cont = json.load(fh)

    n_leads = sum(len(r["findings"])
                  for r in findings["access"] + findings["change"])
    flagged = set()
    for r in findings["access"] + findings["change"]:
        for f in r["findings"]:
            flagged.update(f["record_ids"])
    planted_ids = set()
    for v in manifest["violations"]:
        planted_ids.update(v["refs"].get("grant_ids", []))
        for key in ("ticket_id", "deploy_id"):
            if v["refs"].get(key):
                planted_ids.add(v["refs"][key])
    caught = sum(
        1 for v in manifest["violations"]
        if (set(v["refs"].get("grant_ids", []))
            | {v["refs"][k] for k in ("ticket_id", "deploy_id")
               if v["refs"].get(k)}) & flagged)

    lines = [
        "# examples/run-001",
        "",
        "A committed end-to-end run. Everything here regenerates "
        "byte-identically from `python cli.py example` (bulk exports are "
        "gitignored and rebuilt; manifest, findings, workpapers, card, "
        "and this file are committed).",
        "",
        "## The run",
        "",
        "- Enterprise seed `{0}`: {1} employees on the roster ({6} at "
        "window start, plus joiners) over {2} months, {3} grants, {4} "
        "tickets, {5} deploy-log entries.".format(
            EXAMPLE_SEED,
            cont["comparison"]["population_profile"]["current"]["employees_total"],
            EXAMPLE_CONFIG["months"],
            cont["comparison"]["population_profile"]["current"]["grants_total"],
            cont["comparison"]["population_profile"]["current"]["tickets_total"],
            cont["comparison"]["population_profile"]["current"]["deploys_total"],
            EXAMPLE_CONFIG["employees"]),
        "- {0} planted conditions across {1} classes; the manifest is the "
        "only ground truth.".format(len(manifest["violations"]),
                                    len(manifest["plan"])),
        "- Both engines raised {0} leads; {1} of {2} planted conditions "
        "were flagged in this single run (the statistical claim lives in "
        "the report card, not in one run).".format(
            n_leads, caught, len(manifest["violations"])),
        "",
        "## Report card (5 seeds x 7 per class, floor 0.9)",
        "",
        "- Overall outcome: **{0}** ({1} pass / {2} exception / {3} "
        "inconclusive by class).".format(
            card["overall_outcome"], card["outcome_counts"]["pass"],
            card["outcome_counts"]["exception"],
            card["outcome_counts"]["inconclusive"]),
        "- Precision: {0}".format(card["precision"]["rendered"]),
        "- Clean-population flags, access: {0}".format(
            card["clean_false_positives"]["access"]["per_10k"]["rendered"]),
        "- Clean-population flags, change: {0}".format(
            card["clean_false_positives"]["change"]["per_10k"]["rendered"]),
        "",
        "The card grades the RULES on standard-size populations across "
        "independent seeds; this directory's large enterprise "
        "demonstrates the same engines at scale.",
        "",
        "## Continuous pair ({0} days)".format(EXAMPLE_PRIOR_DAYS),
        "",
        "- New grants: {0}; newly dormant privileged: {1}; open leads: "
        "{2} ({3} persisting, {4} new).".format(
            cont["comparison"]["grants"]["new_n"],
            cont["comparison"]["newly_dormant_privileged"]["n"],
            cont["aging"]["counts"]["open"],
            cont["aging"]["counts"]["persisting"],
            cont["aging"]["counts"]["new"]),
        "",
        "## Files",
        "",
        "- `manifest.json` - planted ground truth (committed)",
        "- `findings.json` - both engines' results (committed)",
        "- `workpapers/`, `leadsheet.*`, `coverage.*` - the workpaper "
        "pack (committed)",
        "- `card.json`, `card.*` - detection report card (committed)",
        "- `continuous.json`, `continuous.*` - snapshot-pair mode "
        "(committed)",
        "- `exports/` - bulk enterprise JSON (gitignored; regenerate "
        "with `python cli.py example --stage generate`)",
        "",
    ]
    path = os.path.join(root, "README.md")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    print("example readme -> " + path)


def cmd_example(args):
    root = args.root
    os.makedirs(root, exist_ok=True)
    stages = (("generate", lambda: _example_generate(root)),
              ("review", lambda: _example_review(root)),
              ("card", lambda: _example_card(root)),
              ("continuous", lambda: _example_continuous(root)),
              ("readme", lambda: _example_readme(root)))
    wanted = [s for s, _ in stages] if args.stage == "all" else [args.stage]
    for name, fn in stages:
        if name in wanted:
            fn()
    return 0


def build_parser():
    ap = argparse.ArgumentParser(prog="itgc-lab", description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="build a synthetic enterprise")
    g.add_argument("--seed", required=True)
    g.add_argument("--out", required=True)
    g.add_argument("--employees", type=int, default=150)
    g.add_argument("--months", type=int, default=18)
    g.add_argument("--snapshot", default="2026-06-30")
    g.add_argument("--tickets-per-month", type=int, default=12)
    g.add_argument("--plant", action="append", metavar="CLASS=N",
                   help="plant N of CLASS (repeatable)")
    g.add_argument("--plant-all", type=int,
                   help="plant N of every class")
    g.add_argument("--plant-seed", help="defaults to --seed")
    g.set_defaults(fn=cmd_generate)

    r = sub.add_parser("review", help="run both engines over an export")
    r.add_argument("--dir", required=True)
    r.add_argument("--out", required=True)
    r.set_defaults(fn=cmd_review)

    c = sub.add_parser("reportcard", help="grade rules on planted truth")
    c.add_argument("--base-seed", default="itgc-rc")
    c.add_argument("--seeds", type=int, default=5)
    c.add_argument("--per-class", type=int, default=7)
    c.add_argument("--floor", type=float, default=0.9)
    c.add_argument("--out", required=True)
    c.set_defaults(fn=cmd_reportcard)

    k = sub.add_parser("continuous", help="snapshot-pair comparison")
    k.add_argument("--dir", required=True)
    k.add_argument("--prior-days", type=int, default=30)
    k.add_argument("--prior-dir")
    k.add_argument("--out", required=True)
    k.set_defaults(fn=cmd_continuous)

    e = sub.add_parser("example", help="rebuild examples/run-001")
    e.add_argument("--root", default=os.path.join("examples", "run-001"))
    e.add_argument("--stage", default="all",
                   choices=["all", "generate", "review", "card",
                            "continuous", "readme"])
    e.set_defaults(fn=cmd_example)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
