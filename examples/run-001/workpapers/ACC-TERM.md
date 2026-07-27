# Workpaper ACC-TERM — Terminated employees with active access

Outcome: exception

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0
- **Rule:** ACC-TERM
- **Outcome:** exception

## Objective and criterion

An account is a lead when its holder's latest employment stint ended in termination more than the grace period before the snapshot and the grant is still active.

## Population

All active user-account grants held by employees present in the HR roster, as of the snapshot (complete examination, no sampling).

Records examined: 20221 of 20221.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Policy thresholds applied

- **termination_grace_days:** 3

## Results of examination

4 lead(s) raised from 20221 records examined.

| Subject | Record id(s) | Rationale |
| --- | --- | --- |
| E-e6aadc30ba | G-043abfeac3 | Account remains active 246 days after the 2025-10-27 termination; the disablement SLA is 3 days. |
| E-64cd70eb1b | G-046c4d451a | Account remains active 53 days after the 2026-05-08 termination; the disablement SLA is 3 days. |
| E-fd59020e69 | G-06f49ee78c | Account remains active 128 days after the 2026-02-22 termination; the disablement SLA is 3 days. |
| E-1baf5fa6ac | G-1bcde552c0 | Account remains active 240 days after the 2025-11-02 termination; the disablement SLA is 3 days. |

## Limitations

- Relies on roster completeness: a termination missing from HR data is invisible to this reconciliation.
- Evaluates the latest employment stint, so rehired employees are not flagged for earlier terminations; a data feed that drops rehire events would change results.
- Grant status is taken from the IAM export; actual authentication activity is not examined.

## Framework references

> References indicate that this procedure produces evidence RELEVANT to the control. They never assert the control is satisfied.

| Control | Original summary | Relevance |
| --- | --- | --- |
| iso-27001-2022:A.5.18 | Access rights are provisioned on business need and removed or adjusted promptly at termination or role change. | Reconciles active grants against roster terminations, evidencing whether rights are removed when employment ends. |
| iso-27001-2022:A.6.5 | Duties that survive termination or role change are defined and enforced, including the removal of what should not survive. | Access persisting past termination is the technical residue the post-employment duties in this control govern. |
| cobit-2019:DSS05.04 | User identities and logical access are managed across their lifecycle so every account traces to a live business need. | Lifecycle evidence: accounts of departed users should leave the active population within the disablement SLA. |
| nist-csf-2.0:PR.AA-01 | Identities and credentials for users, services, and hardware are issued, managed, and revoked by the organization. | Tests the revocation half of identity lifecycle management against the authoritative roster. |

## Certification study tags

- CISA D5-A: Identity and Access Management
