"""Tableau des versions : dernière release et frise de sécurité sur 12 mois, par technologie."""

from dataclasses import dataclass, field
from datetime import date, datetime, time

from django.utils import timezone

from .models import Advisory

MONTHS = 12
# Du moins grave au plus grave : « inconnue » ne masque jamais une sévérité connue.
SEVERITY_RANK = {
    Advisory.Severity.UNKNOWN: 0,
    Advisory.Severity.LOW: 1,
    Advisory.Severity.MODERATE: 2,
    Advisory.Severity.HIGH: 3,
    Advisory.Severity.CRITICAL: 4,
}


@dataclass
class MonthCell:
    start: date
    count: int = 0
    severity: str = ""

    def add(self, severity):
        self.count += 1
        if not self.severity or SEVERITY_RANK.get(severity, 0) > SEVERITY_RANK.get(self.severity, 0):
            self.severity = severity

    @property
    def severity_label(self):
        return Advisory.Severity(self.severity).label if self.severity else ""


@dataclass
class BoardRow:
    technology: object
    latest: object
    months: list = field(default_factory=list)

    @property
    def advisory_count(self):
        return sum(month.count for month in self.months)


def month_starts(today, count=MONTHS):
    """Premier jour des `count` derniers mois, du plus ancien au mois courant."""
    year, month = today.year, today.month
    starts = []
    for _ in range(count):
        starts.append(date(year, month, 1))
        year, month = (year, month - 1) if month > 1 else (year - 1, 12)
    return starts[::-1]


def build_board(technologies, today=None):
    today = today or timezone.localdate()
    starts = month_starts(today)
    since = timezone.make_aware(datetime.combine(starts[0], time.min))
    rows = {
        technology.pk: BoardRow(technology, technology.latest_release(), [MonthCell(start) for start in starts])
        for technology in technologies
    }
    advisories = Advisory.objects.filter(technology__in=list(rows), published_at__gte=since).values_list(
        "technology_id", "published_at", "severity"
    )
    index = {(start.year, start.month): position for position, start in enumerate(starts)}
    for technology_id, published_at, severity in advisories:
        local = timezone.localtime(published_at)
        position = index.get((local.year, local.month))
        if position is not None:
            rows[technology_id].months[position].add(severity)
    return list(rows.values())
