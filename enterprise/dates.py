"""Date arithmetic on ISO strings.

All enterprise data carries dates as ISO 'YYYY-MM-DD' strings; every helper
here is a pure function of its arguments. Nothing in the generator may read
the wall clock (DECISIONS.md D-008): the world is defined entirely by the
configured snapshot date and the seed.
"""

import calendar
from datetime import date, timedelta


def parse(iso: str) -> date:
    return date.fromisoformat(iso)


def iso(dt: date) -> str:
    return dt.isoformat()


def add_days(iso_s: str, n: int) -> str:
    return iso(parse(iso_s) + timedelta(days=n))


def days_between(earlier: str, later: str) -> int:
    """later - earlier, in days (positive when later is after earlier)."""
    return (parse(later) - parse(earlier)).days


def is_weekend(iso_s: str) -> bool:
    return parse(iso_s).weekday() >= 5


def next_business_day(iso_s: str) -> str:
    dt = parse(iso_s)
    while dt.weekday() >= 5:
        dt += timedelta(days=1)
    return iso(dt)


def months_back(iso_s: str, months: int) -> str:
    """Same day-of-month `months` earlier, clamped to month length."""
    dt = parse(iso_s)
    total = dt.year * 12 + (dt.month - 1) - months
    year, month = divmod(total, 12)
    month += 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return iso(date(year, month, day))


def month_starts(start_iso: str, end_iso: str):
    """First-of-month dates covering [start, end], as ISO strings."""
    start, end = parse(start_iso), parse(end_iso)
    out = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        out.append(iso(date(year, month, 1)))
        month += 1
        if month == 13:
            month = 1
            year += 1
    return out


def quarter_ends(start_iso: str, end_iso: str):
    """Calendar quarter-end dates falling within [start, end]."""
    ends = []
    for m_start in month_starts(start_iso, end_iso):
        dt = parse(m_start)
        if dt.month in (3, 6, 9, 12):
            last = date(dt.year, dt.month, calendar.monthrange(dt.year, dt.month)[1])
            if parse(start_iso) <= last <= parse(end_iso):
                ends.append(iso(last))
    return ends


def saturdays(start_iso: str, end_iso: str):
    dt, end = parse(start_iso), parse(end_iso)
    while dt.weekday() != 5:
        dt += timedelta(days=1)
    out = []
    while dt <= end:
        out.append(iso(dt))
        dt += timedelta(days=7)
    return out


def in_window(iso_s: str, start_iso: str, end_iso: str) -> bool:
    return start_iso <= iso_s <= end_iso
