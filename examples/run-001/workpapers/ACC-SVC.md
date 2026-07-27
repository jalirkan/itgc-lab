# Workpaper ACC-SVC — Service and shared account ownership

Outcome: exception

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0
- **Rule:** ACC-SVC
- **Outcome:** exception

## Objective and criterion

A service or shared account is a lead when it has no recorded owner, or its owner is not an active employee.

## Population

All active grants on service and shared accounts (complete examination).

Records examined: 18 of 18.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Policy thresholds applied

This procedure uses no policy thresholds.

## Results of examination

4 lead(s) raised from 18 records examined.

| Subject | Record id(s) | Rationale |
| --- | --- | --- |
| svc-dir-02 | G-785adcbd16 | Service account svc-dir-02 has no recorded owner. |
| svc-crm-01 | G-94436cead2 | Service account svc-crm-01 has no recorded owner. |
| shared-erp-01 | G-ce6e20e761 | Shared account shared-erp-01 has no recorded owner. |
| svc-deploy-01 | G-d011d072cb | Service account svc-deploy-01 has no recorded owner. |

## Limitations

- Ownership is the only hygiene attribute in this export; password rotation, vaulting, and interactive-logon restrictions are not visible here.

## Framework references

> References indicate that this procedure produces evidence RELEVANT to the control. They never assert the control is satisfied.

| Control | Original summary | Relevance |
| --- | --- | --- |
| iso-27001-2022:A.5.16 | Identities are unique, tied to a person or a sanctioned non-human use, and retired when no longer needed. | Non-human identities require sanctioned, current ownership; an unowned account evidences a registration gap. |
| cobit-2019:DSS05.04 | User identities and logical access are managed across their lifecycle so every account traces to a live business need. | Service and shared accounts are lifecycle-managed identities; ownership is the accountability anchor. |
| nist-csf-2.0:PR.AA-01 | Identities and credentials for users, services, and hardware are issued, managed, and revoked by the organization. | Credentials for services are organization-managed only if a live owner answers for them. |

## Certification study tags

- CISA D5-A: Identity and Access Management
