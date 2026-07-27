# Workpaper ACC-SOD — Segregation-of-duties toxic combinations

Outcome: exception

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0
- **Rule:** ACC-SOD
- **Outcome:** exception

## Objective and criterion

A user is a lead when their active grants include both sides of a pair the SoD matrix declares conflicting.

## Population

All roster employees holding at least one active grant, each evaluated against every SoD pair (complete examination at the user level).

Records examined: 5406 of 5406.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Policy thresholds applied

This procedure uses no policy thresholds.

## Results of examination

4 lead(s) raised from 5406 records examined.

| Subject | Record id(s) | Rationale |
| --- | --- | --- |
| E-3c00987e1e | G-38e4cad92e, G-cd098cda49 | User holds both erp:ap-entry and erp:ap-approve. One identity can both create and approve a payable. |
| E-50aaf0f436 | G-5f3f1a07b1, G-b2e8b3abbb | User holds both erp:ap-entry and erp:ap-approve. One identity can both create and approve a payable. |
| E-8103db51a4 | G-755e0ee6c8, G-81f59d1b88 | User holds both deploy:dev-commit and deploy:deploy-approve. One identity can both author a change and approve its release. |
| E-8d41aa1c75 | G-72967429e6, G-8db4b9daab | User holds both erp:gl-post and erp:erp-admin. One identity can both post journal entries and alter ERP controls. |

## Limitations

- Only pairs declared in the SoD matrix are evaluated; conflicts the matrix does not name are not screened.
- The register of cross-functional exceptions does not waive SoD conflicts here: compensating controls are a reviewer judgment outside this data.
- Conflicts across separate accounts of the same person in different systems are matched by employee id only.

## Framework references

> References indicate that this procedure produces evidence RELEVANT to the control. They never assert the control is satisfied.

| Control | Original summary | Relevance |
| --- | --- | --- |
| iso-27001-2022:A.5.3 | Conflicting duties are separated so no single identity can initiate, approve, and conceal the same transaction or change. | Detects one identity holding both sides of a declared conflicting-duty pair across systems. |
| cobit-2019:DSS06.03 | Roles, access privileges, and authority levels stay aligned with assigned duties and their required separations. | Authority levels and their required separations are tested against the declared toxic-pair matrix. |
| nist-csf-2.0:PR.AA-05 | Access permissions are policy-defined, enforced, and reviewed, incorporating least privilege and separation of duties. | Separation of duties is named in this subcategory; the rule evidences its operation in granted access. |

## Certification study tags

- CISA D5-A: Identity and Access Management
