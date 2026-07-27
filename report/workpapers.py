"""Workpaper pack: per-rule workpapers, lead sheet, report card, coverage.

Language discipline is enforced by the renderer, not here — but this
module is written to pass it: exceptions and leads, never verdicts.
Findings and procedures-unable-to-conclude are SEPARATED on the lead
sheet (toolkit D-032): a scope limitation listed among exceptions would
inflate what was established. No wall-clock timestamps anywhere —
document identity is seed + snapshot + versions (lab D-019).
"""

from enterprise.config import GENERATOR_VERSION
from frameworks import catalog
from report.document import bullets, doc, kv, note, p, section, table

LEADS_NOTE = ("Every item in this pack is a lead for auditor follow-up. "
              "These procedures examine recorded data completely and "
              "conclude nothing beyond it; disposition belongs to the "
              "reviewer.")

COMPLETE_EXAM_NOTE = ("Each procedure examines 100 percent of its declared "
                      "population as of the snapshot. Counts are census "
                      "facts about this population, not sample estimates, "
                      "and are always stated with the population size.")


def _identity_kv(ent, extra=None):
    pol = ent["policy"]
    pairs = [
        ("Enterprise seed", pol["seed"]),
        ("Snapshot", pol["snapshot"]),
        ("Window start", pol["window_start"]),
        ("Generator version", pol["generator_version"]),
        ("Workpaper generator", "itgc-lab " + GENERATOR_VERSION),
    ]
    if extra:
        pairs.extend(extra)
    return kv(pairs)


def _cisa_tags(rule_id):
    tags = catalog.rule_map()["rules"][rule_id]["cisa"]
    return ["CISA D{0}-{1}: {2}".format(t["domain"], t["section"], t["topic"])
            for t in tags]


def rule_workpaper(result, ent):
    """One workpaper per rule result."""
    r = result
    blocks_results = []
    if r.refusal_reason is not None:
        blocks_results.append(p(
            "The procedure did not run: {0}. An unrun procedure is an "
            "inconclusive one — it is reported as a scope limitation, "
            "never as a pass.".format(r.refusal_reason)))
    elif not r.findings:
        blocks_results.append(p(
            "No exceptions noted across the complete population of {0} "
            "records.".format(r.population_n)))
    else:
        blocks_results.append(p(
            "{0} lead(s) raised from {1} records examined."
            .format(len(r.findings), r.population_n)))
        blocks_results.append(table(
            ["Subject", "Record id(s)", "Rationale"],
            [[f.subject, ", ".join(f.record_ids), f.rationale]
             for f in r.findings]))

    mappings = catalog.rule_map()["rules"][r.rule_id]["controls"]
    framework_rows = [[m["id"], catalog.control_summary(m["id"]),
                       m["rationale"]] for m in mappings]

    thresholds = (kv(sorted(r.thresholds_used.items()))
                  if r.thresholds_used else p(
                      "This procedure uses no policy thresholds."))

    return doc(
        "Workpaper {0} — {1}".format(r.rule_id, r.title),
        "Outcome: {0}".format(r.outcome),
        section("Identity", _identity_kv(ent, [("Rule", r.rule_id),
                                               ("Outcome", r.outcome)])),
        section("Objective and criterion", p(r.criterion)),
        section("Population", p(r.population_desc),
                p("Records examined: {0} of {1}.".format(
                    r.population_n, r.population_n)),
                note(COMPLETE_EXAM_NOTE)),
        section("Policy thresholds applied", thresholds),
        section("Results of examination", *blocks_results),
        section("Limitations", bullets(r.limitations)),
        section("Framework references",
                note("References indicate that this procedure produces "
                     "evidence RELEVANT to the control. They never assert "
                     "the control is satisfied."),
                table(["Control", "Original summary", "Relevance"],
                      framework_rows)),
        section("Certification study tags", bullets(_cisa_tags(r.rule_id))),
    )


def lead_sheet(access_results, change_results, ent):
    """Engagement lead sheet: exceptions, review leads, and scope
    limitations, separated."""
    everything = list(access_results) + list(change_results)
    summary_rows = [[r.rule_id, r.title, r.outcome, len(r.findings),
                     r.population_n if r.refusal_reason is None else "—"]
                    for r in everything]

    exceptions = [r for r in everything
                  if r.outcome == "exception" and r.rule_id != "CHG-STAL"]
    review_leads = [r for r in everything
                    if r.outcome == "exception" and r.rule_id == "CHG-STAL"]
    unable = [r for r in everything if r.outcome == "inconclusive"]

    sections = [
        section("Identity", _identity_kv(ent)),
        section("Scope and method", p(
            "Two engines ran: an access review over the IAM export "
            "reconciled to the HR roster, and a change-management review "
            "over tickets and the deploy log."), note(COMPLETE_EXAM_NOTE)),
        section("Procedure summary",
                table(["Rule", "Title", "Outcome", "Leads", "Population"],
                      summary_rows)),
    ]

    if exceptions:
        rows = []
        for r in exceptions:
            for f in r.findings:
                rows.append([r.rule_id, f.subject,
                             ", ".join(f.record_ids), f.rationale])
        sections.append(section(
            "Exceptions raised for follow-up",
            p("{0} procedure(s) raised {1} lead(s)."
              .format(len(exceptions), sum(len(r.findings)
                                           for r in exceptions))),
            table(["Rule", "Subject", "Record id(s)", "Rationale"], rows)))
    else:
        sections.append(section(
            "Exceptions raised for follow-up",
            p("No exceptions noted by any procedure that ran.")))

    if review_leads:
        rows = [[f.subject, f.rationale]
                for r in review_leads for f in r.findings]
        sections.append(section(
            "Review leads (recordkeeping)",
            p("Aged approved-but-undeployed tickets are listed apart from "
              "exceptions: they question recordkeeping, not directly a "
              "control's operation."),
            table(["Ticket", "Rationale"], rows)))

    if unable:
        sections.append(section(
            "Procedures unable to conclude (scope limitations)",
            p("Listed separately from exceptions: an unrun procedure "
              "established nothing, in either direction."),
            table(["Rule", "Reason"],
                  [[r.rule_id, r.refusal_reason] for r in unable])))

    sections.append(section("Basis of reporting", note(LEADS_NOTE)))
    return doc("Engagement lead sheet — ITGC review",
               "Access review and change management, complete examinations",
               *sections)


def card_doc(card):
    """Render the detection report card dict as a document."""
    ident = card["identity"]
    plan_values = set(ident["plan"].values())
    plan_desc = (str(plan_values.pop()) if len(plan_values) == 1
                 else "; ".join("{0}={1}".format(k, v)
                                for k, v in sorted(ident["plan"].items())))
    class_rows = []
    for c in card["classes"]:
        class_rows.append([
            c["class"],
            c["planted"],
            c["caught_any"],
            c["recall_any"]["rendered"],
            c["caught_designed"],
            c["decision"]["outcome"],
        ])
    per_seed_rows = []
    for c in card["classes"]:
        for row in c["per_seed"]:
            per_seed_rows.append([c["class"], row["seed"], row["planted"],
                                  row["caught_any"]])
    return doc(
        "Detection report card",
        "Rules graded against planted ground truth across independent seeds",
        section("Identity", kv([
            ("Base seed", ident["base_seed"]),
            ("Seeds", ", ".join(ident["seeds"])),
            ("Planted per class per seed", plan_desc),
            ("Recall floor", ident["recall_floor"]),
            ("Access rules", ", ".join(ident["access_rules"])),
            ("Change rules", ", ".join(ident["change_rules"])),
        ])),
        section("How to read this card", p(
            "A planted condition counts as caught when any rule flags any "
            "of its constituent records; the designed-rule column counts "
            "only the rule built for that class. Recall pools across "
            "seeds and is decided against its Wilson interval: a thin "
            "pool renders inconclusive rather than parading a perfect "
            "rate."), note(
            "There is no composite score. The overall outcome is the "
            "worst class outcome by precedence: exception, then "
            "inconclusive, then pass.")),
        section("Recall by planted class",
                table(["Class", "Planted", "Caught (any)",
                       "Recall (any rule)", "Caught (designed)", "Outcome"],
                      class_rows)),
        section("Precision and false positives", kv([
            ("Precision", card["precision"]["rendered"]),
            ("Clean-population flags, access engine",
             card["clean_false_positives"]["access"]["per_10k"]["rendered"]),
            ("Clean-population flags, change engine",
             card["clean_false_positives"]["change"]["per_10k"]["rendered"]),
        ]), p(
            "Correct reconciliations should flag nothing in a clean "
            "population; the benign look-alikes exist so that a wrong "
            "implementation measurably would. A nonzero clean-population "
            "rate is an implementation regression, not noise.")),
        section("Per-seed stability",
                table(["Class", "Seed", "Planted", "Caught (any)"],
                      per_seed_rows)),
        section("Overall", kv([
            ("Outcome counts", "{0} pass / {1} exception / {2} inconclusive"
             .format(card["outcome_counts"]["pass"],
                     card["outcome_counts"]["exception"],
                     card["outcome_counts"]["inconclusive"])),
            ("Overall outcome", card["overall_outcome"]),
        ])),
    )


def continuous_doc(diff, aging):
    """Render the snapshot-pair comparison and lead aging."""
    win = diff["window"]
    prof = diff["population_profile"]
    profile_rows = []
    for key in sorted(prof["delta"]):
        profile_rows.append([key, prof["prior"][key], prof["current"][key],
                             "{0:+d}".format(prof["delta"][key])])
    open_rows = [[l["rule_id"], l["subject"], l["status"],
                  l["min_age_days"], ", ".join(l["record_ids"])]
                 for l in aging["open_leads"]]
    resolved_rows = [[l["rule_id"], l["subject"],
                      ", ".join(l["record_ids"])]
                     for l in aging["resolved_leads"]]
    rec = diff["recertification"]
    sections = [
        section("Window", kv([
            ("Prior snapshot", win["from"]),
            ("Current snapshot", win["to"]),
            ("Days between", win["days"]),
        ])),
        section("Access deltas", kv([
            ("New grants", "{0} (of {1} active at current)".format(
                diff["grants"]["new_n"], prof["current"]["grants_active"])),
            ("New privileged grants", diff["grants"]["new_privileged_n"]),
            ("Grants removed or disabled", diff["grants"]["removed_n"]),
            ("Newly dormant privileged",
             diff["newly_dormant_privileged"]["n"]),
            ("Terminations in window", len(diff["terminations_in_window"])),
        ])),
        section("Recertification tracking", kv([
            ("Cycle days", rec["cycle_days"]),
            ("Lapsed now", "{0} (prior snapshot: {1})".format(
                rec["lapsed_n"], rec["lapsed_prior_n"])),
            ("Coming due within {0} days".format(
                rec["coming_due_within_days"]), rec["coming_due_n"]),
        ])),
        section("Population profile",
                table(["Metric", "Prior", "Current", "Delta"],
                      profile_rows)),
        section("Open leads", note(aging["note"]),
                kv([("Open", aging["counts"]["open"]),
                    ("New since prior", aging["counts"]["new"]),
                    ("Persisting", aging["counts"]["persisting"]),
                    ("Resolved since prior", aging["counts"]["resolved"])])),
    ]
    if open_rows:
        sections.append(section(
            "Open lead detail",
            table(["Rule", "Subject", "Status", "Min age (days)",
                   "Record id(s)"], open_rows)))
    if resolved_rows:
        sections.append(section(
            "Resolved since prior snapshot",
            table(["Rule", "Subject", "Record id(s)"], resolved_rows)))
    return doc("Continuous monitoring — snapshot pair",
               "Deltas, lead aging, and recertification tracking",
               *sections)


def coverage_doc(cov):
    rows = []
    for entry in cov["controls"]:
        mapped = "; ".join("{0} ({1})".format(m["rule_id"], m["outcome"])
                           for m in entry["mapped_rules"])
        rows.append([entry["control"], entry["summary"],
                     entry["status"], mapped])
    gap_block = (bullets(cov["catalog_controls_with_no_mapped_rule"])
                 if cov["catalog_controls_with_no_mapped_rule"]
                 else p("Every cataloged control is mapped by at least "
                        "one rule."))
    return doc(
        "Framework coverage",
        "What this run evidenced, control by control",
        section("Reading notes",
                note(cov["partiality_note"]),
                note(cov["relevance_note"])),
        section("Controls",
                table(["Control", "Original summary", "Status",
                       "Mapped rules (outcome)"], rows)),
        section("Cataloged controls with no mapped rule", gap_block),
    )
