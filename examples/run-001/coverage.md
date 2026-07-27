# Framework coverage

What this run evidenced, control by control

## Reading notes

> These catalogs list only controls this lab can produce technical evidence for. A control's absence is not a statement about it.

> A mapping asserts that the rule produces evidence RELEVANT to the control - never that the control is satisfied. Every mapping carries its rationale; an unargued mapping cannot be defended in review.

## Controls

| Control | Original summary | Status | Mapped rules (outcome) |
| --- | --- | --- | --- |
| cobit-2019:BAI06.01 | Change requests are evaluated and authorized before implementation, at arm's length from the implementer. | tested-with-exceptions | CHG-APPR (exception); CHG-FRZ (exception); CHG-SELF (exception) |
| cobit-2019:BAI06.02 | Emergency changes take an expedited path whose authorization and review complete promptly after the fact. | tested-with-exceptions | CHG-EMER (exception) |
| cobit-2019:BAI06.03 | Change status is tracked and reported through closure so no request quietly stalls or disappears. | tested-with-exceptions | CHG-STAL (exception); CHG-TICK (exception) |
| cobit-2019:DSS05.04 | User identities and logical access are managed across their lifecycle so every account traces to a live business need. | tested-with-exceptions | ACC-CERT (exception); ACC-DORM (exception); ACC-ORPH (exception); ACC-SVC (exception); ACC-TERM (exception) |
| cobit-2019:DSS06.03 | Roles, access privileges, and authority levels stay aligned with assigned duties and their required separations. | tested-with-exceptions | ACC-AUTH (exception); ACC-SOD (exception) |
| iso-27001-2022:A.5.16 | Identities are unique, tied to a person or a sanctioned non-human use, and retired when no longer needed. | tested-with-exceptions | ACC-ORPH (exception); ACC-SVC (exception) |
| iso-27001-2022:A.5.18 | Access rights are provisioned on business need and removed or adjusted promptly at termination or role change. | tested-with-exceptions | ACC-AUTH (exception); ACC-CERT (exception); ACC-TERM (exception) |
| iso-27001-2022:A.5.3 | Conflicting duties are separated so no single identity can initiate, approve, and conceal the same transaction or change. | tested-with-exceptions | ACC-SOD (exception); CHG-SELF (exception) |
| iso-27001-2022:A.6.5 | Duties that survive termination or role change are defined and enforced, including the removal of what should not survive. | tested-with-exceptions | ACC-TERM (exception) |
| iso-27001-2022:A.8.2 | Privileged rights are restricted, individually justified, and reviewed more often than ordinary access. | tested-with-exceptions | ACC-DORM (exception) |
| iso-27001-2022:A.8.32 | System changes follow a controlled path: recorded request, arm's-length approval, and traceable deployment. | tested-with-exceptions | CHG-APPR (exception); CHG-EMER (exception); CHG-FRZ (exception); CHG-SELF (exception); CHG-STAL (exception); CHG-TICK (exception) |
| nist-csf-2.0:PR.AA-01 | Identities and credentials for users, services, and hardware are issued, managed, and revoked by the organization. | tested-with-exceptions | ACC-ORPH (exception); ACC-SVC (exception); ACC-TERM (exception) |
| nist-csf-2.0:PR.AA-05 | Access permissions are policy-defined, enforced, and reviewed, incorporating least privilege and separation of duties. | tested-with-exceptions | ACC-AUTH (exception); ACC-CERT (exception); ACC-DORM (exception); ACC-SOD (exception); CHG-SELF (exception) |
| nist-csf-2.0:PR.PS-01 | Configuration management practices are established and applied so platforms stay in known, approved states. | tested-with-exceptions | CHG-APPR (exception); CHG-EMER (exception); CHG-FRZ (exception); CHG-STAL (exception); CHG-TICK (exception) |

## Cataloged controls with no mapped rule

Every cataloged control is mapped by at least one rule.
