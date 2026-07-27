# Workpaper CHG-STAL — Approved changes never deployed

Outcome: exception

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0
- **Rule:** CHG-STAL
- **Outcome:** exception

## Objective and criterion

An approved, undeployed ticket is a REVIEW LEAD — a recordkeeping question, not by itself an exception — once its approval is older than the staleness threshold.

## Population

All change tickets with an approval recorded and no matching deploy-log entry (complete examination).

Records examined: 8 of 8.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Policy thresholds applied

- **stale_ticket_days:** 30

## Results of examination

4 lead(s) raised from 8 records examined.

| Subject | Record id(s) | Rationale |
| --- | --- | --- |
| CHG-2b5240978b | CHG-2b5240978b | Change CHG-2b5240978b on deploy was approved 77 days before the snapshot and has no deployment record; the staleness threshold is 30 days. Review lead: confirm disposition with the change owner. |
| CHG-73e125d3eb | CHG-73e125d3eb | Change CHG-73e125d3eb on crm was approved 80 days before the snapshot and has no deployment record; the staleness threshold is 30 days. Review lead: confirm disposition with the change owner. |
| CHG-a12d70ff62 | CHG-a12d70ff62 | Change CHG-a12d70ff62 on hris was approved 83 days before the snapshot and has no deployment record; the staleness threshold is 30 days. Review lead: confirm disposition with the change owner. |
| CHG-dc0736bb81 | CHG-dc0736bb81 | Change CHG-dc0736bb81 on hris was approved 60 days before the snapshot and has no deployment record; the staleness threshold is 30 days. Review lead: confirm disposition with the change owner. |

## Limitations

- An aged open ticket may be legitimately deferred work; this rule measures recordkeeping hygiene, and the lead sheet carries it as a review item rather than an exception to a control.

## Framework references

> References indicate that this procedure produces evidence RELEVANT to the control. They never assert the control is satisfied.

| Control | Original summary | Relevance |
| --- | --- | --- |
| iso-27001-2022:A.8.32 | System changes follow a controlled path: recorded request, arm's-length approval, and traceable deployment. | Approved-but-undeployed tickets aged past threshold evidence recordkeeping drift in the change pipeline. |
| cobit-2019:BAI06.03 | Change status is tracked and reported through closure so no request quietly stalls or disappears. | Tracking through closure is the practice tested; a stalled approved ticket is an untracked ending. |
| nist-csf-2.0:PR.PS-01 | Configuration management practices are established and applied so platforms stay in known, approved states. | Applied practice keeps the recorded pipeline and reality reconciled; stale approvals measure the gap. |

## Certification study tags

- CISA D4-A: IT Change, Configuration, and Patch Management
