# Workpaper ACC-DORM — Dormant privileged access

Outcome: exception

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0
- **Rule:** ACC-DORM
- **Outcome:** exception

## Objective and criterion

A privileged grant is a lead when its last recorded use is older than the dormancy threshold, or when no use is recorded at all.

## Population

All active grants carrying a privileged role, across user, service, and shared accounts (complete examination).

Records examined: 2656 of 2656.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Policy thresholds applied

- **dormant_privileged_days:** 90

## Results of examination

4 lead(s) raised from 2656 records examined.

| Subject | Record id(s) | Rationale |
| --- | --- | --- |
| E-a740855567 | G-6076dfc7c7 | Privileged role deploy-admin on deploy last used 205 days before the snapshot; the dormancy threshold is 90 days. |
| E-5caca08854 | G-764630f184 | Privileged role deploy-admin on deploy last used 166 days before the snapshot; the dormancy threshold is 90 days. |
| E-80715e244e | G-8a9c08bbcf | Privileged role deploy-exec on deploy last used 163 days before the snapshot; the dormancy threshold is 90 days. |
| E-09fd54a051 | G-9f54f965ba | Privileged role deploy-admin on deploy last used 185 days before the snapshot; the dormancy threshold is 90 days. |

## Limitations

- Last-used dates come from the IAM export, not from authentication logs; usage the export does not capture is invisible.
- Dormancy is a staleness screen: legitimate break-glass access can be dormant by design, which is a matter for the reviewer.

## Framework references

> References indicate that this procedure produces evidence RELEVANT to the control. They never assert the control is satisfied.

| Control | Original summary | Relevance |
| --- | --- | --- |
| iso-27001-2022:A.8.2 | Privileged rights are restricted, individually justified, and reviewed more often than ordinary access. | Privileged rights unused past the threshold evidence whether privileged allocation is justified and reviewed. |
| cobit-2019:DSS05.04 | User identities and logical access are managed across their lifecycle so every account traces to a live business need. | Dormant privileged access is lifecycle debt: granted, retained, and unaccounted for in current need. |
| nist-csf-2.0:PR.AA-05 | Access permissions are policy-defined, enforced, and reviewed, incorporating least privilege and separation of duties. | Least privilege implies privileged rights that are actually exercised or removed on review. |

## Certification study tags

- CISA D5-A: Identity and Access Management
