# Workpaper CFG-HARD — Lockout and session hardening against the stated standard

Outcome: exception

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0
- **Rule:** CFG-HARD
- **Outcome:** exception

## Objective and criterion

A recorded lockout or session setting is a lead when its observed value exceeds the maximum the stated standard allows, or when the standard states no requirement for it.

## Population

All recorded account-lockout and session-timeout settings across every system in the configuration baseline (complete examination).

Records examined: 12 of 12.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Policy thresholds applied

- **account_lockout_threshold:** at most 5
- **session_idle_timeout_minutes:** at most 15

## Results of examination

4 lead(s) raised from 12 records examined.

| Subject | Record id(s) | Rationale |
| --- | --- | --- |
| dir | C-05ec679b93 | Setting account_lockout_threshold on dir is recorded as 25; the stated standard requires at most 5. |
| hris | C-08de21c138 | Setting session_idle_timeout_minutes on hris is recorded as 60; the stated standard requires at most 15. |
| deploy | C-284e54e9be | Setting account_lockout_threshold on deploy is recorded as 50; the stated standard requires at most 5. |
| crm | C-af0ba699ef | Setting session_idle_timeout_minutes on crm is recorded as 480; the stated standard requires at most 15. |

## Limitations

- Lockout thresholds and idle timeouts are read from the baseline export; enforcement behaviour is not tested here.
- A single ceiling is applied to every system. Where a system carries a documented tighter or looser requirement, that belongs in the stated standard, not in reviewer memory.

## Framework references

> References indicate that this procedure produces evidence RELEVANT to the control. They never assert the control is satisfied.

| Control | Original summary | Relevance |
| --- | --- | --- |
| iso-27001-2022:A.8.5 | Sign-in is protected by controls proportionate to what the account can reach, including additional factors where the risk warrants them. | Lockout thresholds and idle timeouts are the sign-in protections this control governs; the baseline records what each system actually applies. |
| iso-27001-2022:A.8.9 | Security configuration of systems is defined, applied as a baseline, and monitored for drift away from the approved state. | Hardening values are configuration items: the evidence here is whether they still match the approved baseline. |
| nist-csf-2.0:PR.PS-01 | Configuration management practices are established and applied so platforms stay in known, approved states. | Tests whether platforms remain in the known, approved state the stated standard defines. |

## Certification study tags

- CISA D4-A: IT Change, Configuration, and Patch Management
- CISA D5-A: Identity and Access Management
