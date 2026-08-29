# Workpaper CFG-PWD — Password policy against the stated standard

Outcome: exception

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0
- **Rule:** CFG-PWD
- **Outcome:** exception

## Objective and criterion

A recorded password-policy setting is a lead when its observed value does not satisfy the stated standard's requirement for that setting — a minimum length or history depth, a maximum age — or when the standard states no requirement for it.

## Population

All recorded password-policy settings across every system in the configuration baseline (complete examination).

Records examined: 18 of 18.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Policy thresholds applied

- **password_history_depth:** at least 12
- **password_max_age_days:** at most 90
- **password_min_length:** at least 12

## Results of examination

4 lead(s) raised from 18 records examined.

| Subject | Record id(s) | Rationale |
| --- | --- | --- |
| erp | C-3de3faf093 | Setting password_min_length on erp is recorded as 10; the stated standard requires at least 12. |
| mail | C-889886b419 | Setting password_max_age_days on mail is recorded as 365; the stated standard requires at most 90. |
| mail | C-bfb7cfb026 | Setting password_history_depth on mail is recorded as 3; the stated standard requires at least 12. |
| erp | C-cde016e966 | Setting password_max_age_days on erp is recorded as 180; the stated standard requires at most 90. |

## Limitations

- The baseline records the value each system reports; whether the setting is actually applied to every account on that system is not visible in this export.
- A value stricter than the stated standard satisfies it here. Whether an unusually strict setting is workable in practice is a matter for the reviewer, not a lead.
- Only settings present in the baseline are examined; a system that reports no password policy at all would be a completeness gap in the export rather than a lead here.

## Framework references

> References indicate that this procedure produces evidence RELEVANT to the control. They never assert the control is satisfied.

| Control | Original summary | Relevance |
| --- | --- | --- |
| iso-27001-2022:A.5.17 | Authentication information is issued, held, and changed under rules strong enough that possessing it means what the access decision assumes. | Compares each system's recorded password rules against the standard the organization states, evidencing how authentication information is governed in practice rather than on paper. |
| iso-27001-2022:A.8.9 | Security configuration of systems is defined, applied as a baseline, and monitored for drift away from the approved state. | A password setting that has drifted from the stated baseline is exactly the departure from an approved configuration this control asks to be detected. |
| nist-csf-2.0:PR.PS-01 | Configuration management practices are established and applied so platforms stay in known, approved states. | Reconciles observed platform configuration to the approved state, setting by setting. |

## Certification study tags

- CISA D4-A: IT Change, Configuration, and Patch Management
- CISA D5-A: Identity and Access Management
