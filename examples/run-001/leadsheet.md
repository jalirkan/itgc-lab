# Engagement lead sheet — ITGC review

Access review and change management, complete examinations

## Identity

- **Enterprise seed:** run-001
- **Snapshot:** 2026-06-30
- **Window start:** 2024-12-30
- **Generator version:** 0.1.0
- **Workpaper generator:** itgc-lab 0.1.0

## Scope and method

Three engines ran: an access review over the IAM export reconciled to the HR roster, a change-management review over tickets and the deploy log, and a configuration-baseline review comparing each system's recorded settings and MFA enrolments against the standard this organization states for itself.

> Each procedure examines 100 percent of its declared population as of the snapshot. Counts are census facts about this population, not sample estimates, and are always stated with the population size.

## Procedure summary

| Rule | Title | Outcome | Leads | Population |
| --- | --- | --- | --- | --- |
| ACC-TERM | Terminated employees with active access | exception | 4 | 20221 |
| ACC-ORPH | Accounts with no corresponding employee | exception | 4 | 20225 |
| ACC-DORM | Dormant privileged access | exception | 4 | 2656 |
| ACC-AUTH | Roles outside the authorization matrix | exception | 8 | 20217 |
| ACC-SOD | Segregation-of-duties toxic combinations | exception | 4 | 5406 |
| ACC-SVC | Service and shared account ownership | exception | 4 | 18 |
| ACC-CERT | Access recertification staleness | exception | 4 | 20243 |
| CHG-APPR | Deployed changes without approval | exception | 4 | 695 |
| CHG-SELF | Changes approved by their own developer | exception | 4 | 699 |
| CHG-EMER | Emergency changes without timely post-hoc review | exception | 4 | 7 |
| CHG-TICK | Deploy-log entries with no matching ticket | exception | 4 | 699 |
| CHG-FRZ | Deployments inside change-freeze windows | exception | 4 | 699 |
| CHG-STAL | Approved changes never deployed | exception | 4 | 8 |
| CFG-PWD | Password policy against the stated standard | exception | 4 | 18 |
| CFG-HARD | Lockout and session hardening against the stated standard | exception | 4 | 12 |
| CFG-MFA | Multi-factor authentication enforcement settings | exception | 4 | 12 |
| CFG-ENRL | MFA enrolment of privileged accounts | exception | 4 | 17430 |

## Exceptions raised for follow-up

16 procedure(s) raised 68 lead(s).

| Rule | Subject | Record id(s) | Rationale |
| --- | --- | --- | --- |
| ACC-TERM | E-e6aadc30ba | G-043abfeac3 | Account remains active 246 days after the 2025-10-27 termination; the disablement SLA is 3 days. |
| ACC-TERM | E-64cd70eb1b | G-046c4d451a | Account remains active 53 days after the 2026-05-08 termination; the disablement SLA is 3 days. |
| ACC-TERM | E-fd59020e69 | G-06f49ee78c | Account remains active 128 days after the 2026-02-22 termination; the disablement SLA is 3 days. |
| ACC-TERM | E-1baf5fa6ac | G-1bcde552c0 | Account remains active 240 days after the 2025-11-02 termination; the disablement SLA is 3 days. |
| ACC-ORPH | E-a33962f9a2 | G-05fabb2e1c | Active crm account is assigned to user id E-a33962f9a2, which does not appear in the HR roster for the period. |
| ACC-ORPH | E-fd877fcfb0 | G-5d5704c72f | Active crm account is assigned to user id E-fd877fcfb0, which does not appear in the HR roster for the period. |
| ACC-ORPH | E-88fca28c91 | G-77d78762bf | Active crm account is assigned to user id E-88fca28c91, which does not appear in the HR roster for the period. |
| ACC-ORPH | E-522bd1d286 | G-ad766a4af5 | Active crm account is assigned to user id E-522bd1d286, which does not appear in the HR roster for the period. |
| ACC-DORM | E-a740855567 | G-6076dfc7c7 | Privileged role deploy-admin on deploy last used 205 days before the snapshot; the dormancy threshold is 90 days. |
| ACC-DORM | E-5caca08854 | G-764630f184 | Privileged role deploy-admin on deploy last used 166 days before the snapshot; the dormancy threshold is 90 days. |
| ACC-DORM | E-80715e244e | G-8a9c08bbcf | Privileged role deploy-exec on deploy last used 163 days before the snapshot; the dormancy threshold is 90 days. |
| ACC-DORM | E-09fd54a051 | G-9f54f965ba | Privileged role deploy-admin on deploy last used 185 days before the snapshot; the dormancy threshold is 90 days. |
| ACC-AUTH | E-69a80a2249 | G-260294257f | Role deploy:deploy-approve is outside the authorization matrix for job function sales-operations-analyst, and no recorded exception applies. |
| ACC-AUTH | E-3c00987e1e | G-38e4cad92e | Role erp:ap-approve is outside the authorization matrix for job function accounts-payable-clerk, and no recorded exception applies. |
| ACC-AUTH | E-50aaf0f436 | G-5f3f1a07b1 | Role erp:ap-entry is outside the authorization matrix for job function controller, and no recorded exception applies. |
| ACC-AUTH | E-936517a1b2 | G-6eb0746f54 | Role deploy:deploy-approve is outside the authorization matrix for job function security-analyst, and no recorded exception applies. |
| ACC-AUTH | E-fd399d7f30 | G-7cb9bf828d | Role deploy:dev-commit is outside the authorization matrix for job function system-administrator, and no recorded exception applies. |
| ACC-AUTH | E-8103db51a4 | G-81f59d1b88 | Role deploy:deploy-approve is outside the authorization matrix for job function software-developer, and no recorded exception applies. |
| ACC-AUTH | E-8d41aa1c75 | G-8db4b9daab | Role erp:gl-post is outside the authorization matrix for job function system-administrator, and no recorded exception applies. |
| ACC-AUTH | E-d64af21291 | G-bad9242b73 | Role deploy:dev-commit is outside the authorization matrix for job function security-analyst, and no recorded exception applies. |
| ACC-SOD | E-3c00987e1e | G-38e4cad92e, G-cd098cda49 | User holds both erp:ap-entry and erp:ap-approve. One identity can both create and approve a payable. |
| ACC-SOD | E-50aaf0f436 | G-5f3f1a07b1, G-b2e8b3abbb | User holds both erp:ap-entry and erp:ap-approve. One identity can both create and approve a payable. |
| ACC-SOD | E-8103db51a4 | G-755e0ee6c8, G-81f59d1b88 | User holds both deploy:dev-commit and deploy:deploy-approve. One identity can both author a change and approve its release. |
| ACC-SOD | E-8d41aa1c75 | G-72967429e6, G-8db4b9daab | User holds both erp:gl-post and erp:erp-admin. One identity can both post journal entries and alter ERP controls. |
| ACC-SVC | svc-dir-02 | G-785adcbd16 | Service account svc-dir-02 has no recorded owner. |
| ACC-SVC | svc-crm-01 | G-94436cead2 | Service account svc-crm-01 has no recorded owner. |
| ACC-SVC | shared-erp-01 | G-ce6e20e761 | Shared account shared-erp-01 has no recorded owner. |
| ACC-SVC | svc-deploy-01 | G-d011d072cb | Service account svc-deploy-01 has no recorded owner. |
| ACC-CERT | E-ce6f6d8635 | G-4ebfbd3625 | Grant of user on dir was last recertified 528 days before the snapshot; the cycle is 365 days. |
| ACC-CERT | E-a9e9ff7524 | G-7253580e2f | Grant of crm-user on crm was last recertified 479 days before the snapshot; the cycle is 365 days. |
| ACC-CERT | E-4641f88524 | G-7f3b2b6b93 | Grant of user on dir was last recertified 474 days before the snapshot; the cycle is 365 days. |
| ACC-CERT | E-e6f948f037 | G-c39b06f0a2 | Grant of crm-user on crm was last recertified 516 days before the snapshot; the cycle is 365 days. |
| CHG-APPR | CHG-42b2d71050 | CHG-42b2d71050, DPL-952cfcb9b8 | Change CHG-42b2d71050 on deploy was deployed 2025-10-27 with no approval recorded on the ticket. |
| CHG-APPR | CHG-b7d7345e53 | CHG-b7d7345e53, DPL-6d472a5703 | Change CHG-b7d7345e53 on hris was deployed 2026-04-08 with no approval recorded on the ticket. |
| CHG-APPR | CHG-d71439be17 | CHG-d71439be17, DPL-3ee3e35549 | Change CHG-d71439be17 on deploy was deployed 2025-02-21 with no approval recorded on the ticket. |
| CHG-APPR | CHG-f8b56c1b61 | CHG-f8b56c1b61, DPL-e28e0bba6e | Change CHG-f8b56c1b61 on hris was deployed 2026-02-23 with no approval recorded on the ticket. |
| CHG-SELF | CHG-19e44d6feb | CHG-19e44d6feb, DPL-38710be701 | Change CHG-19e44d6feb on deploy records E-358fd0b48c as both developer and approver. |
| CHG-SELF | CHG-2cfced7ea3 | CHG-2cfced7ea3, DPL-2f486bdf3d | Change CHG-2cfced7ea3 on hris records E-23c41499be as both developer and approver. |
| CHG-SELF | CHG-78420afc49 | CHG-78420afc49, DPL-70a01fff93 | Change CHG-78420afc49 on deploy records E-2ac1fa74a9 as both developer and approver. |
| CHG-SELF | CHG-eb3207cd7e | CHG-eb3207cd7e, DPL-da8058330a | Change CHG-eb3207cd7e on hris records E-50d1ec0025 as both developer and approver. |
| CHG-EMER | CHG-27625fa5a6 | CHG-27625fa5a6, DPL-d40b3c0cf3 | Emergency change CHG-27625fa5a6 on crm was deployed 2026-03-28, and no post-hoc review is recorded within the 5-day window. |
| CHG-EMER | CHG-cc5bce6c47 | CHG-cc5bce6c47, DPL-ad99256c8d | Emergency change CHG-cc5bce6c47 on crm was deployed 2026-01-24, and no post-hoc review is recorded within the 5-day window. |
| CHG-EMER | CHG-e32c950179 | CHG-e32c950179, DPL-db3abcdee3 | Emergency change CHG-e32c950179 on deploy was deployed 2025-01-18, and no post-hoc review is recorded within the 5-day window. |
| CHG-EMER | CHG-eb027dc2ea | CHG-eb027dc2ea, DPL-2962a916b6 | Emergency change CHG-eb027dc2ea on erp was deployed 2025-05-10, and no post-hoc review is recorded within the 5-day window. |
| CHG-TICK | DPL-08fe2154e3 | DPL-08fe2154e3 | Deployment to hris on 2025-08-07 by E-d2bd3ca7a6 references ticket id CHG-7357527ca1, which does not exist in the ticket system. |
| CHG-TICK | DPL-4cc0a0cdc6 | DPL-4cc0a0cdc6 | Deployment to deploy on 2025-08-26 by E-ee1a6af417 references ticket id CHG-223e8631de, which does not exist in the ticket system. |
| CHG-TICK | DPL-d063886b3d | DPL-d063886b3d | Deployment to hris on 2026-03-04 by E-bdcbcc7d50 references ticket id CHG-6b653aee8d, which does not exist in the ticket system. |
| CHG-TICK | DPL-d1d33cf719 | DPL-d1d33cf719 | Deployment to erp on 2025-08-06 by E-25057126d1 references ticket id CHG-62d624da92, which does not exist in the ticket system. |
| CHG-FRZ | DPL-1be92174b3 | CHG-d186ec64fd, DPL-1be92174b3 | Deployment to erp on 2025-03-29 falls inside the freeze window 2025-03-29 to 2025-03-31 (Quarter-end change freeze). |
| CHG-FRZ | DPL-1f861f5a59 | CHG-b63615661c, DPL-1f861f5a59 | Deployment to deploy on 2025-12-30 falls inside the freeze window 2025-12-29 to 2025-12-31 (Quarter-end change freeze). |
| CHG-FRZ | DPL-7c773b8e54 | CHG-85b190bd54, DPL-7c773b8e54 | Deployment to hris on 2025-12-30 falls inside the freeze window 2025-12-29 to 2025-12-31 (Quarter-end change freeze). |
| CHG-FRZ | DPL-940ae6b125 | CHG-6c7bb19553, DPL-940ae6b125 | Deployment to hris on 2025-03-30 falls inside the freeze window 2025-03-29 to 2025-03-31 (Quarter-end change freeze). |
| CFG-PWD | erp | C-3de3faf093 | Setting password_min_length on erp is recorded as 10; the stated standard requires at least 12. |
| CFG-PWD | mail | C-889886b419 | Setting password_max_age_days on mail is recorded as 365; the stated standard requires at most 90. |
| CFG-PWD | mail | C-bfb7cfb026 | Setting password_history_depth on mail is recorded as 3; the stated standard requires at least 12. |
| CFG-PWD | erp | C-cde016e966 | Setting password_max_age_days on erp is recorded as 180; the stated standard requires at most 90. |
| CFG-HARD | dir | C-05ec679b93 | Setting account_lockout_threshold on dir is recorded as 25; the stated standard requires at most 5. |
| CFG-HARD | hris | C-08de21c138 | Setting session_idle_timeout_minutes on hris is recorded as 60; the stated standard requires at most 15. |
| CFG-HARD | deploy | C-284e54e9be | Setting account_lockout_threshold on deploy is recorded as 50; the stated standard requires at most 5. |
| CFG-HARD | crm | C-af0ba699ef | Setting session_idle_timeout_minutes on crm is recorded as 480; the stated standard requires at most 15. |
| CFG-MFA | dir | C-33a2265297 | Setting mfa_required_for_privileged on dir is recorded as False; the stated standard requires set to True. |
| CFG-MFA | deploy | C-76e0da8538 | Setting mfa_required_for_privileged on deploy is recorded as False; the stated standard requires set to True. |
| CFG-MFA | crm | C-984722dd21 | Setting mfa_required_for_privileged on crm is recorded as False; the stated standard requires set to True. |
| CFG-MFA | deploy | C-c55430cade | Setting mfa_required_for_remote_access on deploy is recorded as False; the stated standard requires set to True. |
| CFG-ENRL | E-436c7523b2 | M-a310832dda | Account E-436c7523b2 on dir holds privileged access and the enrolment register records no multi-factor enrolment for it; the stated standard requires MFA for privileged access. |
| CFG-ENRL | E-e2f8337f62 | M-b9ec0da224 | Account E-e2f8337f62 on mail holds privileged access and the enrolment register records no multi-factor enrolment for it; the stated standard requires MFA for privileged access. |
| CFG-ENRL | E-69c62b6ce1 | M-ea8a511c05 | Account E-69c62b6ce1 on deploy holds privileged access and the enrolment register records no multi-factor enrolment for it; the stated standard requires MFA for privileged access. |
| CFG-ENRL | E-4c0437807e | M-f7b6a98a56 | Account E-4c0437807e on deploy holds privileged access and the enrolment register records no multi-factor enrolment for it; the stated standard requires MFA for privileged access. |

## Review leads (recordkeeping)

Aged approved-but-undeployed tickets are listed apart from exceptions: they question recordkeeping, not directly a control's operation.

| Ticket | Rationale |
| --- | --- |
| CHG-2b5240978b | Change CHG-2b5240978b on deploy was approved 77 days before the snapshot and has no deployment record; the staleness threshold is 30 days. Review lead: confirm disposition with the change owner. |
| CHG-73e125d3eb | Change CHG-73e125d3eb on crm was approved 80 days before the snapshot and has no deployment record; the staleness threshold is 30 days. Review lead: confirm disposition with the change owner. |
| CHG-a12d70ff62 | Change CHG-a12d70ff62 on hris was approved 83 days before the snapshot and has no deployment record; the staleness threshold is 30 days. Review lead: confirm disposition with the change owner. |
| CHG-dc0736bb81 | Change CHG-dc0736bb81 on hris was approved 60 days before the snapshot and has no deployment record; the staleness threshold is 30 days. Review lead: confirm disposition with the change owner. |

## Basis of reporting

> Every item in this pack is a lead for auditor follow-up. These procedures examine recorded data completely and conclude nothing beyond it; disposition belongs to the reviewer.
