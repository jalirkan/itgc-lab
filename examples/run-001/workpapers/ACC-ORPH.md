# Workpaper ACC-ORPH — Accounts with no corresponding employee

Outcome: exception

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0
- **Rule:** ACC-ORPH
- **Outcome:** exception

## Objective and criterion

An active user account is a lead when its user id does not appear anywhere in the HR roster for the period.

## Population

All active user-account grants in the IAM export, reconciled against the full HR roster (complete examination).

Records examined: 20225 of 20225.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Policy thresholds applied

This procedure uses no policy thresholds.

## Results of examination

4 lead(s) raised from 20225 records examined.

| Subject | Record id(s) | Rationale |
| --- | --- | --- |
| E-a33962f9a2 | G-05fabb2e1c | Active crm account is assigned to user id E-a33962f9a2, which does not appear in the HR roster for the period. |
| E-fd877fcfb0 | G-5d5704c72f | Active crm account is assigned to user id E-fd877fcfb0, which does not appear in the HR roster for the period. |
| E-88fca28c91 | G-77d78762bf | Active crm account is assigned to user id E-88fca28c91, which does not appear in the HR roster for the period. |
| E-522bd1d286 | G-ad766a4af5 | Active crm account is assigned to user id E-522bd1d286, which does not appear in the HR roster for the period. |

## Limitations

- Reconciliation is by user id: an account mapped to the wrong employee id would not be flagged here.
- Contractors or system identities absent from the HR feed by design would appear as leads; the reviewer disposes of them with the population owner.

## Framework references

> References indicate that this procedure produces evidence RELEVANT to the control. They never assert the control is satisfied.

| Control | Original summary | Relevance |
| --- | --- | --- |
| iso-27001-2022:A.5.16 | Identities are unique, tied to a person or a sanctioned non-human use, and retired when no longer needed. | An active account with no roster identity evidences a gap in identity registration or retirement. |
| cobit-2019:DSS05.04 | User identities and logical access are managed across their lifecycle so every account traces to a live business need. | Every account must trace to a live business need; an unmatched account has none on record. |
| nist-csf-2.0:PR.AA-01 | Identities and credentials for users, services, and hardware are issued, managed, and revoked by the organization. | Organization-managed identities imply no unaccounted-for credentials in the population. |

## Certification study tags

- CISA D5-A: Identity and Access Management
