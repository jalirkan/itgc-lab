"""Enterprise orchestrator: one seed in, one coherent org out.

Every component draws from its own string-seeded stream (DECISIONS.md
D-006/D-007): "roster", "iam", "tickets" — and the injector, elsewhere,
"violations". Artifacts are plain JSON-shaped dicts written through
core.canonical, so "same seed, same enterprise" is byte identity, not a
summary claim (per lab D-007 / toolkit D-009). No wall clock anywhere:
the world is a pure function of (config, data files, code version).
"""

import os

from . import catalogs, iam, roster, tickets
from .config import GENERATOR_VERSION, THRESHOLDS, GenConfig
from . import dates
from core import rng as rngmod
from core.canonical import SCHEMA_VERSION, read_canonical, write_canonical

ARTIFACTS = ("roster", "iam", "tickets", "deploys", "exceptions", "policy")


def generate(cfg: GenConfig):
    """Build the clean enterprise. Returns dict of artifact-name -> dict."""
    org_data = catalogs.org()
    matrix = catalogs.authorization_matrix()

    employees, terminations = roster.build_roster(
        rngmod.stream(cfg.seed, "roster"), cfg, org_data)
    grants, exceptions = iam.build_iam(
        rngmod.stream(cfg.seed, "iam"), cfg, THRESHOLDS, employees, matrix)
    ticket_rows, deploy_rows, freezes = tickets.build_tickets(
        rngmod.stream(cfg.seed, "tickets"), cfg, THRESHOLDS, employees)

    window_start = dates.months_back(cfg.snapshot, cfg.months)
    return {
        "roster": {
            "schema_version": SCHEMA_VERSION,
            "kind": "roster",
            "employees": employees,
            "terminations": terminations,
        },
        "iam": {
            "schema_version": SCHEMA_VERSION,
            "kind": "iam",
            "grants": grants,
        },
        "tickets": {
            "schema_version": SCHEMA_VERSION,
            "kind": "tickets",
            "tickets": ticket_rows,
        },
        "deploys": {
            "schema_version": SCHEMA_VERSION,
            "kind": "deploys",
            "deploys": deploy_rows,
        },
        "exceptions": {
            "schema_version": SCHEMA_VERSION,
            "kind": "exceptions",
            "exceptions": exceptions,
        },
        "policy": {
            "schema_version": SCHEMA_VERSION,
            "kind": "policy",
            "generator_version": GENERATOR_VERSION,
            "seed": cfg.seed,
            "snapshot": cfg.snapshot,
            "window_start": window_start,
            "config": cfg.to_dict(),
            "thresholds": dict(THRESHOLDS),
            "freeze_windows": freezes,
        },
    }


def write(enterprise, outdir):
    os.makedirs(outdir, exist_ok=True)
    for name in ARTIFACTS:
        write_canonical(os.path.join(outdir, name + ".json"), enterprise[name])


def load(outdir):
    ent = {}
    for name in ARTIFACTS:
        path = os.path.join(outdir, name + ".json")
        ent[name] = read_canonical(path)
        if ent[name].get("schema_version", 0) > SCHEMA_VERSION:
            raise ValueError(
                "artifact {0} has schema_version {1}, newer than supported {2}"
                .format(name, ent[name]["schema_version"], SCHEMA_VERSION))
    manifest_path = os.path.join(outdir, "manifest.json")
    if os.path.exists(manifest_path):
        ent["manifest"] = read_canonical(manifest_path)
    return ent
