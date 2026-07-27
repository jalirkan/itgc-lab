# Workpaper ACC-CERT — Access recertification staleness

Outcome: exception

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0
- **Rule:** ACC-CERT
- **Outcome:** exception

## Objective and criterion

An active grant is a lead when its last recertification is older than the recertification cycle, or missing.

## Population

All active grants across user, service, and shared accounts (complete examination).

Records examined: 20243 of 20243.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Policy thresholds applied

- **recert_cycle_days:** 365

## Results of examination

4 lead(s) raised from 20243 records examined.

| Subject | Record id(s) | Rationale |
| --- | --- | --- |
| E-ce6f6d8635 | G-4ebfbd3625 | Grant of user on dir was last recertified 528 days before the snapshot; the cycle is 365 days. |
| E-a9e9ff7524 | G-7253580e2f | Grant of crm-user on crm was last recertified 479 days before the snapshot; the cycle is 365 days. |
| E-4641f88524 | G-7f3b2b6b93 | Grant of user on dir was last recertified 474 days before the snapshot; the cycle is 365 days. |
| E-e6f948f037 | G-c39b06f0a2 | Grant of crm-user on crm was last recertified 516 days before the snapshot; the cycle is 365 days. |

## Limitations

- Certification dates attest that a review was recorded, not that it was substantive.

## Framework references

> References indicate that this procedure produces evidence RELEVANT to the control. They never assert the control is satisfied.

| Control | Original summary | Relevance |
| --- | --- | --- |
| iso-27001-2022:A.5.18 | Access rights are provisioned on business need and removed or adjusted promptly at termination or role change. | Recertification dates evidence the recurring review of access rights this control expects. |
| cobit-2019:DSS05.04 | User identities and logical access are managed across their lifecycle so every account traces to a live business need. | Periodic review is part of the access lifecycle; lapsed certification dates evidence the cycle not operating. |
| nist-csf-2.0:PR.AA-05 | Access permissions are policy-defined, enforced, and reviewed, incorporating least privilege and separation of duties. | Reviewed permissions require a review cadence; staleness is measured against the declared cycle. |

## Certification study tags

- CISA D5-A: Identity and Access Management
