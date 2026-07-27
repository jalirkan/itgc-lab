# Workpaper CHG-FRZ — Deployments inside change-freeze windows

Outcome: exception

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0
- **Rule:** CHG-FRZ
- **Outcome:** exception

## Objective and criterion

A deploy-log entry is a lead when its deployment date falls inside a declared change-freeze window.

## Population

All deploy-log entries, tested against every declared freeze window (complete examination).

Records examined: 699 of 699.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Policy thresholds applied

This procedure uses no policy thresholds.

## Results of examination

4 lead(s) raised from 699 records examined.

| Subject | Record id(s) | Rationale |
| --- | --- | --- |
| DPL-1be92174b3 | CHG-d186ec64fd, DPL-1be92174b3 | Deployment to erp on 2025-03-29 falls inside the freeze window 2025-03-29 to 2025-03-31 (Quarter-end change freeze). |
| DPL-1f861f5a59 | CHG-b63615661c, DPL-1f861f5a59 | Deployment to deploy on 2025-12-30 falls inside the freeze window 2025-12-29 to 2025-12-31 (Quarter-end change freeze). |
| DPL-7c773b8e54 | CHG-85b190bd54, DPL-7c773b8e54 | Deployment to hris on 2025-12-30 falls inside the freeze window 2025-12-29 to 2025-12-31 (Quarter-end change freeze). |
| DPL-940ae6b125 | CHG-6c7bb19553, DPL-940ae6b125 | Deployment to hris on 2025-03-30 falls inside the freeze window 2025-03-29 to 2025-03-31 (Quarter-end change freeze). |

## Limitations

- Freeze windows are taken from policy data; ad-hoc freezes announced elsewhere are invisible.
- No exemption mechanism exists in this data: an authorized in-freeze deployment would still surface as a lead for the reviewer to dispose of.

## Framework references

> References indicate that this procedure produces evidence RELEVANT to the control. They never assert the control is satisfied.

| Control | Original summary | Relevance |
| --- | --- | --- |
| iso-27001-2022:A.8.32 | System changes follow a controlled path: recorded request, arm's-length approval, and traceable deployment. | Declared freeze windows are part of the controlled schedule; deployments inside them evidence the schedule not operating. |
| cobit-2019:BAI06.01 | Change requests are evaluated and authorized before implementation, at arm's length from the implementer. | A deployment during a declared freeze proceeded against the standing authorization calendar. |
| nist-csf-2.0:PR.PS-01 | Configuration management practices are established and applied so platforms stay in known, approved states. | Freeze adherence is applied configuration management on the calendar dimension. |

## Certification study tags

- CISA D4-A: IT Change, Configuration, and Patch Management
- CISA D3-B: Implementation Configuration and Release Management
