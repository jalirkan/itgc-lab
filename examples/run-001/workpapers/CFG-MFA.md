# Workpaper CFG-MFA — Multi-factor authentication enforcement settings

Outcome: exception

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0
- **Rule:** CFG-MFA
- **Outcome:** exception

## Objective and criterion

A recorded MFA enforcement setting is a lead when the stated standard requires it to be enabled and the system reports it as not enabled, or when the standard states no requirement for it.

## Population

All recorded MFA enforcement settings — privileged access and remote access — across every system in the configuration baseline (complete examination).

Records examined: 12 of 12.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Policy thresholds applied

- **mfa_required_for_privileged:** set to True
- **mfa_required_for_remote_access:** set to True

## Results of examination

4 lead(s) raised from 12 records examined.

| Subject | Record id(s) | Rationale |
| --- | --- | --- |
| dir | C-33a2265297 | Setting mfa_required_for_privileged on dir is recorded as False; the stated standard requires set to True. |
| deploy | C-76e0da8538 | Setting mfa_required_for_privileged on deploy is recorded as False; the stated standard requires set to True. |
| crm | C-984722dd21 | Setting mfa_required_for_privileged on crm is recorded as False; the stated standard requires set to True. |
| deploy | C-c55430cade | Setting mfa_required_for_remote_access on deploy is recorded as False; the stated standard requires set to True. |

## Limitations

- This procedure examines whether the requirement is switched on, not which factors are accepted or how they may be bypassed.
- Whether accounts are actually enrolled is a separate population and is examined by CFG-ENRL, not here.

## Framework references

> References indicate that this procedure produces evidence RELEVANT to the control. They never assert the control is satisfied.

| Control | Original summary | Relevance |
| --- | --- | --- |
| iso-27001-2022:A.8.5 | Sign-in is protected by controls proportionate to what the account can reach, including additional factors where the risk warrants them. | Whether a system requires an additional authentication factor is the protection this control is about; the rule reads that switch per system. |
| iso-27001-2022:A.8.9 | Security configuration of systems is defined, applied as a baseline, and monitored for drift away from the approved state. | An MFA requirement recorded as switched off is a departure from the approved configuration baseline. |
| nist-csf-2.0:PR.PS-01 | Configuration management practices are established and applied so platforms stay in known, approved states. | Evidence that the configuration carrying the stated standard is actually in place on each platform. |

## Certification study tags

- CISA D4-A: IT Change, Configuration, and Patch Management
- CISA D5-A: Identity and Access Management
