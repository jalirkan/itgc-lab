"""Framework catalogs, rule→control map, and coverage reporting.

Discipline (DECISIONS.md D-016, per toolkit D-003/D-025/D-026/D-027):
- catalogs hold control IDs plus ORIGINAL one-line summaries, capped in
  length and scanned for long quoted spans, so pasted framework text
  cannot arrive silently;
- catalogs are partial and say so — only controls this lab can produce
  technical evidence for;
- a mapping asserts relevance of evidence, never satisfaction, and
  cannot exist without a written rationale;
- coverage reports the rule outcomes next to every mapping and lists
  gaps explicitly.
"""

import json
import os
import re
from functools import lru_cache

MAX_SUMMARY_CHARS = 220
MAX_QUOTED_SPAN = 60

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


class CatalogError(ValueError):
    pass


@lru_cache(maxsize=None)
def _load(name):
    with open(os.path.join(_DATA_DIR, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


def controls():
    return _load("controls.json")


def rule_map():
    return _load("rule_map.json")


def control_summary(qualified_id):
    catalog_id, _, control_id = qualified_id.partition(":")
    cats = controls()["catalogs"]
    if catalog_id not in cats:
        raise CatalogError("unknown catalog: " + catalog_id)
    if control_id not in cats[catalog_id]["controls"]:
        raise CatalogError("unknown control: " + qualified_id)
    return cats[catalog_id]["controls"][control_id]


_QUOTED = re.compile(r'"([^"]{%d,})"|“([^”]{%d,})”'
                     % (MAX_QUOTED_SPAN, MAX_QUOTED_SPAN))


def validate_catalogs(data=None):
    """Raise CatalogError on any summary that could be pasted text."""
    data = data or controls()
    for catalog_id, cat in sorted(data["catalogs"].items()):
        for control_id, summary in sorted(cat["controls"].items()):
            if len(summary) > MAX_SUMMARY_CHARS:
                raise CatalogError(
                    "{0}:{1} summary exceeds {2} chars — an original "
                    "one-liner fits, pasted framework text does not"
                    .format(catalog_id, control_id, MAX_SUMMARY_CHARS))
            if _QUOTED.search(summary):
                raise CatalogError(
                    "{0}:{1} summary contains a quoted span of {2}+ chars — "
                    "quoting is how copyrighted text would arrive"
                    .format(catalog_id, control_id, MAX_QUOTED_SPAN))
    if "partiality" not in data.get("verified", {}):
        raise CatalogError("catalogs must state their partiality")
    return True


def validate_map(data=None, known_rule_ids=None):
    """Every mapping resolves, carries a rationale, and covers every rule."""
    data = data or rule_map()
    for rule_id, entry in sorted(data["rules"].items()):
        if not entry.get("controls"):
            raise CatalogError(rule_id + " maps to no controls")
        for ref in entry["controls"]:
            if not ref.get("rationale", "").strip():
                raise CatalogError(
                    "{0} -> {1}: a mapping without a rationale cannot be "
                    "defended in review".format(rule_id, ref.get("id")))
            control_summary(ref["id"])  # raises on unknown ids
        if not entry.get("cisa"):
            raise CatalogError(rule_id + " carries no CISA outline tag")
        for tag in entry["cisa"]:
            if set(tag) != {"domain", "section", "topic"}:
                raise CatalogError(rule_id + " has a malformed CISA tag")
    if known_rule_ids is not None:
        missing = set(known_rule_ids) - set(data["rules"])
        if missing:
            raise CatalogError(
                "rules without framework mappings: " + ", ".join(sorted(missing)))
        extra = set(data["rules"]) - set(known_rule_ids)
        if extra:
            raise CatalogError(
                "mappings for unknown rules: " + ", ".join(sorted(extra)))
    return True


def coverage(results):
    """Control-by-control view of what the run evidenced.

    Status precedence per control: exception > pass > inconclusive —
    reported next to each mapped rule's own outcome, so a control shown
    as covered-and-failing is distinguishable from covered (toolkit
    D-027). Controls in the catalog that no rule maps to are listed as
    gaps rather than omitted.
    """
    by_rule = {r.rule_id: r for r in results}
    per_control = {}
    for rule_id, entry in sorted(rule_map()["rules"].items()):
        res = by_rule.get(rule_id)
        for ref in entry["controls"]:
            slot = per_control.setdefault(ref["id"], [])
            slot.append({
                "rule_id": rule_id,
                "outcome": res.outcome if res else "not-run",
                "findings_n": len(res.findings) if res else 0,
                "rationale": ref["rationale"],
            })
    rows = []
    for qualified_id in sorted(per_control):
        mapped = per_control[qualified_id]
        outcomes = {m["outcome"] for m in mapped}
        if "exception" in outcomes:
            status = "tested-with-exceptions"
        elif "pass" in outcomes:
            status = "tested-no-exceptions-noted"
        elif outcomes == {"not-run"}:
            status = "not-run"
        else:
            status = "inconclusive"
        rows.append({"control": qualified_id,
                     "summary": control_summary(qualified_id),
                     "status": status, "mapped_rules": mapped})
    all_controls = set()
    for catalog_id, cat in controls()["catalogs"].items():
        for control_id in cat["controls"]:
            all_controls.add("{0}:{1}".format(catalog_id, control_id))
    unmapped = sorted(all_controls - set(per_control))
    return {
        "partiality_note": controls()["verified"]["partiality"],
        "relevance_note": rule_map()["note"],
        "controls": rows,
        "catalog_controls_with_no_mapped_rule": unmapped,
    }
