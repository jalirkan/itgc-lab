# examples/run-001

A committed end-to-end run. Everything here regenerates byte-identically from `python cli.py example` (bulk exports are gitignored and rebuilt; manifest, findings, workpapers, card, and this file are committed).

## The run

- Enterprise seed `run-001`: 5900 employees on the roster (5000 at window start, plus joiners) over 18 months, 23545 grants, 703 tickets, 699 deploy-log entries.
- 68 planted conditions across 17 classes; the manifest is the only ground truth.
- The three engines raised 72 leads; 68 of 68 planted conditions were flagged in this single run (the statistical claim lives in the report card, not in one run).

## Report card (5 seeds x 7 per class, floor 0.9)

- Overall outcome: **pass** (17 pass / 0 exception / 0 inconclusive by class).
- Precision: record-level precision on planted populations: 770/770 = 100.0% (95% Wilson 99.5%-100.0%, n=770)
- Clean-population flags, access: 0.0 per 10k (95% Wilson 0.0-10.5 per 10k, n=3660)
- Clean-population flags, change: 0.0 per 10k (95% Wilson 0.0-18.1 per 10k, n=2118)
- Clean-population flags, baseline: 0.0 per 10k (95% Wilson 0.0-13.0 per 10k, n=2944)

The card grades the RULES on standard-size populations across independent seeds; this directory's large enterprise demonstrates the same engines at scale.

## Continuous pair (30 days)

- New grants: 188; newly dormant privileged: 0; open leads: 56 (55 persisting, 1 new).

## Files

- `manifest.json` - planted ground truth (committed)
- `findings.json` - every engine's results (committed)
- `workpapers/`, `leadsheet.*`, `coverage.*` - the workpaper pack (committed)
- `card.json`, `card.*` - detection report card (committed)
- `continuous.json`, `continuous.*` - snapshot-pair mode (committed)
- `exports/` - bulk enterprise JSON (gitignored; regenerate with `python cli.py example --stage generate`)
