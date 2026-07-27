# Workpaper CHG-TICK — Deploy-log entries with no matching ticket

Outcome: exception

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0
- **Rule:** CHG-TICK
- **Outcome:** exception

## Objective and criterion

A deploy-log entry is a lead when it references no ticket, or references a ticket id that does not exist in the ticket system.

## Population

All deploy-log entries, reconciled against the full ticket export (complete examination).

Records examined: 699 of 699.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Policy thresholds applied

This procedure uses no policy thresholds.

## Results of examination

4 lead(s) raised from 699 records examined.

| Subject | Record id(s) | Rationale |
| --- | --- | --- |
| DPL-08fe2154e3 | DPL-08fe2154e3 | Deployment to hris on 2025-08-07 by E-d2bd3ca7a6 references ticket id CHG-7357527ca1, which does not exist in the ticket system. |
| DPL-4cc0a0cdc6 | DPL-4cc0a0cdc6 | Deployment to deploy on 2025-08-26 by E-ee1a6af417 references ticket id CHG-223e8631de, which does not exist in the ticket system. |
| DPL-d063886b3d | DPL-d063886b3d | Deployment to hris on 2026-03-04 by E-bdcbcc7d50 references ticket id CHG-6b653aee8d, which does not exist in the ticket system. |
| DPL-d1d33cf719 | DPL-d1d33cf719 | Deployment to erp on 2025-08-06 by E-25057126d1 references ticket id CHG-62d624da92, which does not exist in the ticket system. |

## Limitations

- Reconciliation is by ticket id: a deploy attached to the WRONG ticket reconciles cleanly and is not caught here.

## Framework references

> References indicate that this procedure produces evidence RELEVANT to the control. They never assert the control is satisfied.

| Control | Original summary | Relevance |
| --- | --- | --- |
| iso-27001-2022:A.8.32 | System changes follow a controlled path: recorded request, arm's-length approval, and traceable deployment. | A deploy with no ticket is a change with no recorded request or approval - outside the controlled path entirely. |
| cobit-2019:BAI06.03 | Change status is tracked and reported through closure so no request quietly stalls or disappears. | Tracking through closure fails loudly when the deployment log holds entries the ticket system never saw. |
| nist-csf-2.0:PR.PS-01 | Configuration management practices are established and applied so platforms stay in known, approved states. | Log-versus-ticket reconciliation evidences whether configuration management practice covers all deployments. |

## Certification study tags

- CISA D4-A: IT Change, Configuration, and Patch Management
