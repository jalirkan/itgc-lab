# Workpaper CHG-EMER — Emergency changes without timely post-hoc review

Outcome: exception

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0
- **Rule:** CHG-EMER
- **Outcome:** exception

## Objective and criterion

A deployed emergency change is a lead when no post-hoc review is recorded, when the review falls outside the SLA window after deployment, or when the reviewer is the developer.

## Population

All emergency change tickets with a matching deploy-log entry (complete examination).

Records examined: 7 of 7.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Policy thresholds applied

- **emergency_review_days:** 5

## Results of examination

4 lead(s) raised from 7 records examined.

| Subject | Record id(s) | Rationale |
| --- | --- | --- |
| CHG-27625fa5a6 | CHG-27625fa5a6, DPL-d40b3c0cf3 | Emergency change CHG-27625fa5a6 on crm was deployed 2026-03-28, and no post-hoc review is recorded within the 5-day window. |
| CHG-cc5bce6c47 | CHG-cc5bce6c47, DPL-ad99256c8d | Emergency change CHG-cc5bce6c47 on crm was deployed 2026-01-24, and no post-hoc review is recorded within the 5-day window. |
| CHG-e32c950179 | CHG-e32c950179, DPL-db3abcdee3 | Emergency change CHG-e32c950179 on deploy was deployed 2025-01-18, and no post-hoc review is recorded within the 5-day window. |
| CHG-eb027dc2ea | CHG-eb027dc2ea, DPL-2962a916b6 | Emergency change CHG-eb027dc2ea on erp was deployed 2025-05-10, and no post-hoc review is recorded within the 5-day window. |

## Limitations

- The review is evidenced by two ticket fields; its substance is not examined.
- Properly-reviewed emergencies deployed on weekends are expected and are not leads.

## Framework references

> References indicate that this procedure produces evidence RELEVANT to the control. They never assert the control is satisfied.

| Control | Original summary | Relevance |
| --- | --- | --- |
| iso-27001-2022:A.8.32 | System changes follow a controlled path: recorded request, arm's-length approval, and traceable deployment. | Expedited changes remain inside the controlled path only if reviewed promptly after the fact. |
| cobit-2019:BAI06.02 | Emergency changes take an expedited path whose authorization and review complete promptly after the fact. | The emergency-change practice is tested directly: post-hoc review present, timely, and independent. |
| nist-csf-2.0:PR.PS-01 | Configuration management practices are established and applied so platforms stay in known, approved states. | Emergency paths are part of applied configuration management practice, not an exemption from it. |

## Certification study tags

- CISA D4-A: IT Change, Configuration, and Patch Management
