# Workpaper CFG-ENRL — MFA enrolment of privileged accounts

Outcome: exception

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0
- **Rule:** CFG-ENRL
- **Outcome:** exception

## Objective and criterion

An enrolment-register row is a lead when the account holds active privileged access, the stated standard requires multi-factor authentication for privileged access, and the register records no enrolment for it.

## Population

The complete MFA enrolment register: one row per account holding at least one active grant, privileged and ordinary alike (complete examination).

Records examined: 17430 of 17430.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Policy thresholds applied

- **mfa_required_for_privileged:** set to True

## Results of examination

4 lead(s) raised from 17430 records examined.

| Subject | Record id(s) | Rationale |
| --- | --- | --- |
| E-436c7523b2 | M-a310832dda | Account E-436c7523b2 on dir holds privileged access and the enrolment register records no multi-factor enrolment for it; the stated standard requires MFA for privileged access. |
| E-e2f8337f62 | M-b9ec0da224 | Account E-e2f8337f62 on mail holds privileged access and the enrolment register records no multi-factor enrolment for it; the stated standard requires MFA for privileged access. |
| E-69c62b6ce1 | M-ea8a511c05 | Account E-69c62b6ce1 on deploy holds privileged access and the enrolment register records no multi-factor enrolment for it; the stated standard requires MFA for privileged access. |
| E-4c0437807e | M-f7b6a98a56 | Account E-4c0437807e on deploy holds privileged access and the enrolment register records no multi-factor enrolment for it; the stated standard requires MFA for privileged access. |

## Limitations

- Ordinary accounts appear in this population and are not leads: the stated standard requires MFA for privileged access, so an unenrolled ordinary account is outside the criterion, not an exception to it.
- Enrolment is evidenced by the register; whether the enrolled factor is ever challenged at sign-in is not visible here.
- Accounts absent from the register are not examined by this procedure — register completeness against the access export is not reconciled here.

## Framework references

> References indicate that this procedure produces evidence RELEVANT to the control. They never assert the control is satisfied.

| Control | Original summary | Relevance |
| --- | --- | --- |
| iso-27001-2022:A.8.2 | Privileged rights are restricted, individually justified, and reviewed more often than ordinary access. | Privileged rights carry the strongest authentication expectation; the register shows which privileged accounts actually carry a second factor. |
| iso-27001-2022:A.8.5 | Sign-in is protected by controls proportionate to what the account can reach, including additional factors where the risk warrants them. | Examines the population the sign-in protection applies to, rather than the setting that requires it. |
| nist-csf-2.0:PR.AA-01 | Identities and credentials for users, services, and hardware are issued, managed, and revoked by the organization. | Credential management evidence: a privileged identity whose second factor was never issued is an unmanaged credential. |

## Certification study tags

- CISA D5-A: Identity and Access Management
