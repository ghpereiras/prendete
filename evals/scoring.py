"""Scores a draft against the expected answer for one eval case, field by field. Pure code: no network."""
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from app.plan_draft import DEFAULT_TZ
from app.schemas.ai import PlanDraft

# Compared on every case (a missing expectation means "none expected", so "somos 10" must not become a limit).
ALWAYS = ("kind", "dates", "max_attendees")
# Compared only when the case states them.
OPTIONAL = ("title", "location", "description", "duration_minutes", "warnings")


def normalize(text: str | None) -> str:
    """Lower-case and accent-free, so "Álamos" matches "alamos"."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()


def local_minutes(moment: datetime) -> str:
    return moment.astimezone(ZoneInfo(DEFAULT_TZ)).strftime("%Y-%m-%dT%H:%M")


@dataclass
class CaseScore:
    case_id: str
    fields: dict[str, bool] = field(default_factory=dict)
    details: dict[str, str] = field(default_factory=dict)
    error: str | None = None
    raw: dict | None = None  # what the model actually returned, to see whether a miss is the model or our rules

    @property
    def passed(self) -> bool:
        return self.error is None and all(self.fields.values())


def _contains_all(haystack: str | None, needles: list[str]) -> bool:
    text = normalize(haystack)
    return all(normalize(needle) in text for needle in needles)


def score(case: dict, draft: PlanDraft) -> CaseScore:
    expect = case["expect"]
    result = CaseScore(case["id"])

    def check(name: str, ok: bool, got, wanted) -> None:
        result.fields[name] = ok
        if not ok:
            result.details[name] = f"expected {wanted!r}, got {got!r}"

    check("kind", draft.kind == expect["kind"], draft.kind, expect["kind"])
    got_dates = [local_minutes(d) for d in draft.dates]
    check("dates", got_dates == sorted(expect["dates"]), got_dates, sorted(expect["dates"]))
    wanted_cap = expect.get("max_attendees")
    check("max_attendees", draft.max_attendees == wanted_cap, draft.max_attendees, wanted_cap)

    if "title_has" in expect:
        check("title", _contains_all(draft.title, expect["title_has"]), draft.title, expect["title_has"])
    if "location_has" in expect:
        check("location", _contains_all(draft.location, expect["location_has"]), draft.location, expect["location_has"])
    if "description_has" in expect:
        check("description", _contains_all(draft.description, expect["description_has"]), draft.description, expect["description_has"])
    if "duration_minutes" in expect:
        check("duration_minutes", draft.duration_minutes == expect["duration_minutes"], draft.duration_minutes, expect["duration_minutes"])
    if "warnings" in expect:
        check("warnings", sorted(draft.warnings) == sorted(expect["warnings"]), sorted(draft.warnings), sorted(expect["warnings"]))
    return result


def summarize(scores: list[CaseScore]) -> dict:
    """Pass rate overall and accuracy per field, counting only the cases that exercise each field."""
    per_field: dict[str, list[bool]] = {}
    for s in scores:
        for name, ok in s.fields.items():
            per_field.setdefault(name, []).append(ok)
    return {
        "cases": len(scores),
        "passed": sum(s.passed for s in scores),
        "errors": sum(s.error is not None for s in scores),
        "pass_rate": (sum(s.passed for s in scores) / len(scores)) if scores else 0.0,
        "per_field": {name: (sum(v) / len(v), len(v)) for name, v in sorted(per_field.items())},
    }
