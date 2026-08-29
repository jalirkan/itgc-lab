"""Language and bare-rate guards, enforced AT THE RENDERER (D-003).

Findings are leads. Rendered documents therefore refuse two vocabularies
(per lab D-003/D-024, extended here):

- conclusory audit language — a determination the evidence cannot make
  ("fraud", "violation", "noncompliant" as verdicts);
- incident language — an access anomaly is an audit exception, not an
  incident declaration ("breach", "compromised", "attacker").

The planted-class identifiers (e.g. "change.freeze_violation") are ground
-truth vocabulary: the injector KNOWS it planted a violation, and the
identifiers may appear verbatim in report-card tables. They are stripped
before scanning (an exact-string allowlist, the same shape as lab
D-024's allowance for standard titles), and the ban applies to prose.
The allowlist is derived from CLASSES, so a planted class added later is
covered without anyone remembering to widen a literal list.

The bare-rate rule (toolkit D-030): any rendered line containing a
percent sign must also carry its n (as "n=" or a k/n fraction). Census
counts render as "12 of 341", so the only percent signs that appear come
from Measurements, which always carry n.
"""

import re

from enterprise.violations import CLASSES

PROHIBITED = (
    # conclusory determinations
    r"frauds?", r"fraudulent", r"guilty", r"criminal", r"neglig\w*",
    r"violat\w*", r"non-?complian\w*", r"control\s+fail\w*",
    # incident language
    r"breach\w*", r"compromis\w*", r"hack\w*", r"attack\w*",
    r"malicious", r"intrusion\w*", r"exfiltrat\w*", r"incidents?",
)

_PROHIBITED_RE = re.compile(
    r"\b(?:" + "|".join(PROHIBITED) + r")\b", re.IGNORECASE)

_PCT_LINE_OK = re.compile(r"n=\d|\b\d+\s*/\s*\d+\b|\b\d+ of \d+\b")


class GuardError(ValueError):
    pass


def _strip_allowlisted(text):
    for cls in CLASSES:
        text = text.replace(cls, " ")
    return text


def check_language(text):
    stripped = _strip_allowlisted(text)
    hit = _PROHIBITED_RE.search(stripped)
    if hit:
        line = next((l for l in stripped.splitlines()
                     if hit.group(0) in l), "")
        raise GuardError(
            "prohibited term {0!r} in rendered output — findings are "
            "leads, not determinations or incident declarations (D-003). "
            "Line: {1!r}".format(hit.group(0), line.strip()[:120]))
    return True


def check_rates(text):
    for line in text.splitlines():
        if "%" in line and not _PCT_LINE_OK.search(line):
            raise GuardError(
                "line shows a percentage without its n (toolkit D-030 "
                "discipline): {0!r}".format(line.strip()[:120]))
    return True


def check_offline(html_text):
    for needle in ("http://", "https://", "<script", "<link"):
        if needle in html_text:
            raise GuardError(
                "rendered HTML must be self-contained and fetch nothing; "
                "found {0!r}".format(needle))
    return True


def check_document_text(text):
    check_language(text)
    check_rates(text)
    return True
