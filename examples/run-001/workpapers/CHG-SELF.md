# Workpaper CHG-SELF — Changes approved by their own developer

Outcome: exception

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0
- **Rule:** CHG-SELF
- **Outcome:** exception

## Objective and criterion

A ticket is a lead when the recorded approver is the same person as the recorded developer.

## Population

All change tickets carrying both a developer and an approver (complete examination).

Records examined: 699 of 699.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Policy thresholds applied

This procedure uses no policy thresholds.

## Results of examination

4 lead(s) raised from 699 records examined.

| Subject | Record id(s) | Rationale |
| --- | --- | --- |
| CHG-19e44d6feb | CHG-19e44d6feb, DPL-38710be701 | Change CHG-19e44d6feb on deploy records E-358fd0b48c as both developer and approver. |
| CHG-2cfced7ea3 | CHG-2cfced7ea3, DPL-2f486bdf3d | Change CHG-2cfced7ea3 on hris records E-23c41499be as both developer and approver. |
| CHG-78420afc49 | CHG-78420afc49, DPL-70a01fff93 | Change CHG-78420afc49 on deploy records E-2ac1fa74a9 as both developer and approver. |
| CHG-eb3207cd7e | CHG-eb3207cd7e, DPL-da8058330a | Change CHG-eb3207cd7e on hris records E-50d1ec0025 as both developer and approver. |

## Limitations

- Identity is matched on employee id; the same human behind two ids would not be caught here.
- Requester/approver overlap is not screened — the segregation examined is develop-versus-approve.

## Framework references

> References indicate that this procedure produces evidence RELEVANT to the control. They never assert the control is satisfied.

| Control | Original summary | Relevance |
| --- | --- | --- |
| iso-27001-2022:A.5.3 | Conflicting duties are separated so no single identity can initiate, approve, and conceal the same transaction or change. | Developer-approves-own-change is a conflicting-duty pairing inside the change process. |
| iso-27001-2022:A.8.32 | System changes follow a controlled path: recorded request, arm's-length approval, and traceable deployment. | Arm's-length approval is part of the controlled change path this rule evidences. |
| cobit-2019:BAI06.01 | Change requests are evaluated and authorized before implementation, at arm's length from the implementer. | Authorization at arm's length from the implementer is tested by the approver/developer identity match. |
| nist-csf-2.0:PR.AA-05 | Access permissions are policy-defined, enforced, and reviewed, incorporating least privilege and separation of duties. | Separation of duties applies to change roles as much as to financial ones. |

## Certification study tags

- CISA D4-A: IT Change, Configuration, and Patch Management
