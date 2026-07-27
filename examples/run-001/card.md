# Detection report card

Rules graded against planted ground truth across independent seeds

## Identity

- **Base seed:** itgc-rc
- **Seeds:** itgc-rc-001, itgc-rc-002, itgc-rc-003, itgc-rc-004, itgc-rc-005
- **Planted per class per seed:** 7
- **Recall floor:** 0.9
- **Access rules:** ACC-TERM, ACC-ORPH, ACC-DORM, ACC-AUTH, ACC-SOD, ACC-SVC, ACC-CERT
- **Change rules:** CHG-APPR, CHG-SELF, CHG-EMER, CHG-TICK, CHG-FRZ, CHG-STAL

## How to read this card

A planted condition counts as caught when any rule flags any of its constituent records; the designed-rule column counts only the rule built for that class. Recall pools across seeds and is decided against its Wilson interval: a thin pool renders inconclusive rather than parading a perfect rate.

> There is no composite score. The overall outcome is the worst class outcome by precedence: exception, then inconclusive, then pass.

## Recall by planted class

| Class | Planted | Caught (any) | Recall (any rule) | Caught (designed) | Outcome |
| --- | --- | --- | --- | --- | --- |
| access.dormant_privileged | 35 | 35 | recall (any rule): access.dormant_privileged: 35/35 = 100.0% (95% Wilson 90.1%-100.0%, n=35) | 35 | pass |
| access.orphan_account | 35 | 35 | recall (any rule): access.orphan_account: 35/35 = 100.0% (95% Wilson 90.1%-100.0%, n=35) | 35 | pass |
| access.recert_lapsed | 35 | 35 | recall (any rule): access.recert_lapsed: 35/35 = 100.0% (95% Wilson 90.1%-100.0%, n=35) | 35 | pass |
| access.role_mismatch | 35 | 35 | recall (any rule): access.role_mismatch: 35/35 = 100.0% (95% Wilson 90.1%-100.0%, n=35) | 35 | pass |
| access.service_account_no_owner | 35 | 35 | recall (any rule): access.service_account_no_owner: 35/35 = 100.0% (95% Wilson 90.1%-100.0%, n=35) | 35 | pass |
| access.sod_conflict | 35 | 35 | recall (any rule): access.sod_conflict: 35/35 = 100.0% (95% Wilson 90.1%-100.0%, n=35) | 35 | pass |
| access.terminated_active | 35 | 35 | recall (any rule): access.terminated_active: 35/35 = 100.0% (95% Wilson 90.1%-100.0%, n=35) | 35 | pass |
| change.deploy_without_ticket | 35 | 35 | recall (any rule): change.deploy_without_ticket: 35/35 = 100.0% (95% Wilson 90.1%-100.0%, n=35) | 35 | pass |
| change.emergency_no_review | 35 | 35 | recall (any rule): change.emergency_no_review: 35/35 = 100.0% (95% Wilson 90.1%-100.0%, n=35) | 35 | pass |
| change.freeze_violation | 35 | 35 | recall (any rule): change.freeze_violation: 35/35 = 100.0% (95% Wilson 90.1%-100.0%, n=35) | 35 | pass |
| change.missing_approval | 35 | 35 | recall (any rule): change.missing_approval: 35/35 = 100.0% (95% Wilson 90.1%-100.0%, n=35) | 35 | pass |
| change.self_approval | 35 | 35 | recall (any rule): change.self_approval: 35/35 = 100.0% (95% Wilson 90.1%-100.0%, n=35) | 35 | pass |
| change.stale_ticket | 35 | 35 | recall (any rule): change.stale_ticket: 35/35 = 100.0% (95% Wilson 90.1%-100.0%, n=35) | 35 | pass |

## Precision and false positives

- **Precision:** record-level precision on planted populations: 630/630 = 100.0% (95% Wilson 99.4%-100.0%, n=630)
- **Clean-population flags, access engine:** 0.0 per 10k (95% Wilson 0.0-10.5 per 10k, n=3660)
- **Clean-population flags, change engine:** 0.0 per 10k (95% Wilson 0.0-18.1 per 10k, n=2118)

Correct reconciliations should flag nothing in a clean population; the benign look-alikes exist so that a wrong implementation measurably would. A nonzero clean-population rate is an implementation regression, not noise.

## Per-seed stability

| Class | Seed | Planted | Caught (any) |
| --- | --- | --- | --- |
| access.dormant_privileged | itgc-rc-001 | 7 | 7 |
| access.dormant_privileged | itgc-rc-002 | 7 | 7 |
| access.dormant_privileged | itgc-rc-003 | 7 | 7 |
| access.dormant_privileged | itgc-rc-004 | 7 | 7 |
| access.dormant_privileged | itgc-rc-005 | 7 | 7 |
| access.orphan_account | itgc-rc-001 | 7 | 7 |
| access.orphan_account | itgc-rc-002 | 7 | 7 |
| access.orphan_account | itgc-rc-003 | 7 | 7 |
| access.orphan_account | itgc-rc-004 | 7 | 7 |
| access.orphan_account | itgc-rc-005 | 7 | 7 |
| access.recert_lapsed | itgc-rc-001 | 7 | 7 |
| access.recert_lapsed | itgc-rc-002 | 7 | 7 |
| access.recert_lapsed | itgc-rc-003 | 7 | 7 |
| access.recert_lapsed | itgc-rc-004 | 7 | 7 |
| access.recert_lapsed | itgc-rc-005 | 7 | 7 |
| access.role_mismatch | itgc-rc-001 | 7 | 7 |
| access.role_mismatch | itgc-rc-002 | 7 | 7 |
| access.role_mismatch | itgc-rc-003 | 7 | 7 |
| access.role_mismatch | itgc-rc-004 | 7 | 7 |
| access.role_mismatch | itgc-rc-005 | 7 | 7 |
| access.service_account_no_owner | itgc-rc-001 | 7 | 7 |
| access.service_account_no_owner | itgc-rc-002 | 7 | 7 |
| access.service_account_no_owner | itgc-rc-003 | 7 | 7 |
| access.service_account_no_owner | itgc-rc-004 | 7 | 7 |
| access.service_account_no_owner | itgc-rc-005 | 7 | 7 |
| access.sod_conflict | itgc-rc-001 | 7 | 7 |
| access.sod_conflict | itgc-rc-002 | 7 | 7 |
| access.sod_conflict | itgc-rc-003 | 7 | 7 |
| access.sod_conflict | itgc-rc-004 | 7 | 7 |
| access.sod_conflict | itgc-rc-005 | 7 | 7 |
| access.terminated_active | itgc-rc-001 | 7 | 7 |
| access.terminated_active | itgc-rc-002 | 7 | 7 |
| access.terminated_active | itgc-rc-003 | 7 | 7 |
| access.terminated_active | itgc-rc-004 | 7 | 7 |
| access.terminated_active | itgc-rc-005 | 7 | 7 |
| change.deploy_without_ticket | itgc-rc-001 | 7 | 7 |
| change.deploy_without_ticket | itgc-rc-002 | 7 | 7 |
| change.deploy_without_ticket | itgc-rc-003 | 7 | 7 |
| change.deploy_without_ticket | itgc-rc-004 | 7 | 7 |
| change.deploy_without_ticket | itgc-rc-005 | 7 | 7 |
| change.emergency_no_review | itgc-rc-001 | 7 | 7 |
| change.emergency_no_review | itgc-rc-002 | 7 | 7 |
| change.emergency_no_review | itgc-rc-003 | 7 | 7 |
| change.emergency_no_review | itgc-rc-004 | 7 | 7 |
| change.emergency_no_review | itgc-rc-005 | 7 | 7 |
| change.freeze_violation | itgc-rc-001 | 7 | 7 |
| change.freeze_violation | itgc-rc-002 | 7 | 7 |
| change.freeze_violation | itgc-rc-003 | 7 | 7 |
| change.freeze_violation | itgc-rc-004 | 7 | 7 |
| change.freeze_violation | itgc-rc-005 | 7 | 7 |
| change.missing_approval | itgc-rc-001 | 7 | 7 |
| change.missing_approval | itgc-rc-002 | 7 | 7 |
| change.missing_approval | itgc-rc-003 | 7 | 7 |
| change.missing_approval | itgc-rc-004 | 7 | 7 |
| change.missing_approval | itgc-rc-005 | 7 | 7 |
| change.self_approval | itgc-rc-001 | 7 | 7 |
| change.self_approval | itgc-rc-002 | 7 | 7 |
| change.self_approval | itgc-rc-003 | 7 | 7 |
| change.self_approval | itgc-rc-004 | 7 | 7 |
| change.self_approval | itgc-rc-005 | 7 | 7 |
| change.stale_ticket | itgc-rc-001 | 7 | 7 |
| change.stale_ticket | itgc-rc-002 | 7 | 7 |
| change.stale_ticket | itgc-rc-003 | 7 | 7 |
| change.stale_ticket | itgc-rc-004 | 7 | 7 |
| change.stale_ticket | itgc-rc-005 | 7 | 7 |

## Overall

- **Outcome counts:** 13 pass / 0 exception / 0 inconclusive
- **Overall outcome:** pass
