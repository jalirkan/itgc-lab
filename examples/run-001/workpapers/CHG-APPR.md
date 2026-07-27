# Workpaper CHG-APPR — Deployed changes without approval

Outcome: exception

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0
- **Rule:** CHG-APPR
- **Outcome:** exception

## Objective and criterion

A deployed change is a lead when no approval is recorded at all, or — for non-emergency changes — when the recorded approval postdates the deployment.

## Population

All change tickets with at least one matching deploy-log entry (complete examination).

Records examined: 695 of 695.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Policy thresholds applied

This procedure uses no policy thresholds.

## Results of examination

4 lead(s) raised from 695 records examined.

| Subject | Record id(s) | Rationale |
| --- | --- | --- |
| CHG-42b2d71050 | CHG-42b2d71050, DPL-952cfcb9b8 | Change CHG-42b2d71050 on deploy was deployed 2025-10-27 with no approval recorded on the ticket. |
| CHG-b7d7345e53 | CHG-b7d7345e53, DPL-6d472a5703 | Change CHG-b7d7345e53 on hris was deployed 2026-04-08 with no approval recorded on the ticket. |
| CHG-d71439be17 | CHG-d71439be17, DPL-3ee3e35549 | Change CHG-d71439be17 on deploy was deployed 2025-02-21 with no approval recorded on the ticket. |
| CHG-f8b56c1b61 | CHG-f8b56c1b61, DPL-e28e0bba6e | Change CHG-f8b56c1b61 on hris was deployed 2026-02-23 with no approval recorded on the ticket. |

## Limitations

- Approval is evidenced by ticket fields only; an approval given out-of-band and never recorded is indistinguishable from none.
- Emergency changes are expected to be approved after deployment; their post-hoc review is examined by CHG-EMER, not here.

## Framework references

> References indicate that this procedure produces evidence RELEVANT to the control. They never assert the control is satisfied.

| Control | Original summary | Relevance |
| --- | --- | --- |
| iso-27001-2022:A.8.32 | System changes follow a controlled path: recorded request, arm's-length approval, and traceable deployment. | Deployments lacking recorded approval evidence changes travelling outside the controlled path. |
| cobit-2019:BAI06.01 | Change requests are evaluated and authorized before implementation, at arm's length from the implementer. | Authorization-before-implementation is the practice tested by reconciling approvals to deploy dates. |
| nist-csf-2.0:PR.PS-01 | Configuration management practices are established and applied so platforms stay in known, approved states. | Applied configuration management implies production changes carry recorded, prior authorization. |

## Certification study tags

- CISA D4-A: IT Change, Configuration, and Patch Management
