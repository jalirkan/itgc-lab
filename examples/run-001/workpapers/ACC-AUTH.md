# Workpaper ACC-AUTH — Roles outside the authorization matrix

Outcome: exception

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0
- **Rule:** ACC-AUTH
- **Outcome:** exception

## Objective and criterion

An active grant is a lead when its role is not authorized for the holder's current job function and no unexpired recorded exception covers it.

## Population

All active user-account grants held by roster employees whose employment stint is open at the snapshot (complete examination).

Records examined: 20217 of 20217.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Policy thresholds applied

This procedure uses no policy thresholds.

## Results of examination

8 lead(s) raised from 20217 records examined.

| Subject | Record id(s) | Rationale |
| --- | --- | --- |
| E-69a80a2249 | G-260294257f | Role deploy:deploy-approve is outside the authorization matrix for job function sales-operations-analyst, and no recorded exception applies. |
| E-3c00987e1e | G-38e4cad92e | Role erp:ap-approve is outside the authorization matrix for job function accounts-payable-clerk, and no recorded exception applies. |
| E-50aaf0f436 | G-5f3f1a07b1 | Role erp:ap-entry is outside the authorization matrix for job function controller, and no recorded exception applies. |
| E-936517a1b2 | G-6eb0746f54 | Role deploy:deploy-approve is outside the authorization matrix for job function security-analyst, and no recorded exception applies. |
| E-fd399d7f30 | G-7cb9bf828d | Role deploy:dev-commit is outside the authorization matrix for job function system-administrator, and no recorded exception applies. |
| E-8103db51a4 | G-81f59d1b88 | Role deploy:deploy-approve is outside the authorization matrix for job function software-developer, and no recorded exception applies. |
| E-8d41aa1c75 | G-8db4b9daab | Role erp:gl-post is outside the authorization matrix for job function system-administrator, and no recorded exception applies. |
| E-d64af21291 | G-bad9242b73 | Role deploy:dev-commit is outside the authorization matrix for job function security-analyst, and no recorded exception applies. |

## Limitations

- The matrix is evaluated against the holder's job function at the snapshot; access that was proper under a prior function appears here once the function changes.
- Recorded exceptions are honored at face value; whether an exception SHOULD have been granted is a reviewer judgment.
- A job function absent from the matrix yields a coverage lead for every grant its holders carry, not a pass.

## Framework references

> References indicate that this procedure produces evidence RELEVANT to the control. They never assert the control is satisfied.

| Control | Original summary | Relevance |
| --- | --- | --- |
| iso-27001-2022:A.5.18 | Access rights are provisioned on business need and removed or adjusted promptly at termination or role change. | Grants compared to the function-based matrix evidence provisioning on business need, exception-managed otherwise. |
| cobit-2019:DSS06.03 | Roles, access privileges, and authority levels stay aligned with assigned duties and their required separations. | Role-aligned privileges are the criterion this rule reconciles grant-by-grant against the matrix. |
| nist-csf-2.0:PR.AA-05 | Access permissions are policy-defined, enforced, and reviewed, incorporating least privilege and separation of duties. | Policy-defined and reviewed permissions are tested directly against the recorded authorization policy. |

## Certification study tags

- CISA D5-A: Identity and Access Management
